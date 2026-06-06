import re
import yaml
from typing import Dict, List, Optional, Any, Tuple
from app.models.novel import NovelInput
from app.models.screenplay import (
    Screenplay, ScreenplayMeta, CharacterRef, Act, Scene,
    ContentBlock, ContinuityWarning
)
from app.services.converter import ContextHub


class Assembler:
    """Phase 2: Merges, validates, and assembles per-chapter YAML into a complete Screenplay."""

    def assemble(self, novel: NovelInput, chapter_yamls: Dict[int, str],
                 context: ContextHub) -> Optional[Screenplay]:
        all_characters = self._merge_characters(chapter_yamls, context)
        continuity_warnings = []

        # Flatten all scenes from all chapters
        all_scenes = []
        for ch_idx in sorted(chapter_yamls.keys()):
            yaml_text = chapter_yamls[ch_idx]
            scenes = self._parse_scenes(yaml_text, ch_idx, context)
            all_scenes.extend(scenes)

        # Re-number scenes sequentially
        for i, scene in enumerate(all_scenes, 1):
            scene.number = i
            scene.id = f"scene_{i:03d}"

        # Continuity checks
        for w in self._check_orphan_characters(all_scenes, all_characters):
            continuity_warnings.append(w)
        for w in self._check_location_consistency(all_scenes):
            continuity_warnings.append(w)
        for w in self._check_scene_gaps(all_scenes):
            continuity_warnings.append(w)
        for w in self._check_character_descriptions(chapter_yamls, context):
            continuity_warnings.append(w)
        for w in context.continuity_warnings:
            continuity_warnings.append(w)

        # Group scenes into acts (by chapter boundaries)
        acts = self._build_acts(all_scenes, novel)

        meta = ScreenplayMeta(
            title=novel.title,
            source=novel.title,
            author=novel.author,
            chapter_count=len(novel.chapters),
        )

        return Screenplay(
            metadata=meta,
            characters=all_characters,
            acts=acts,
            warnings=continuity_warnings,
        )

    def _merge_characters(self, chapter_yamls: Dict[int, str],
                          context: ContextHub) -> List[CharacterRef]:
        """Step 1 - Exact match, Step 2 - Alias match, Step 3 - Fuzzy match."""
        merged: Dict[str, CharacterRef] = {}

        # Collect all character entries from all chapters
        all_entries = []
        for ch_yaml in chapter_yamls.values():
            try:
                data = yaml.safe_load(ch_yaml)
                if data and "characters" in data:
                    all_entries.extend(data["characters"])
            except yaml.YAMLError:
                pass

        # Also include pre-scan characters
        for pc in context.characters:
            existing = [e for e in all_entries if e.get("name") == pc.get("name")]
            if not existing:
                all_entries.append(pc)

        # Step 1: Exact name match
        # Track a counter for generating unique IDs for entries without one
        id_counter = 1
        for entry in all_entries:
            name = entry.get("name", "")
            if not name:
                continue
            if name in merged:
                self._merge_fields(merged[name], _to_char_ref(entry, id_counter))
            else:
                merged[name] = _to_char_ref(entry, id_counter)
                id_counter += 1

        # Step 2: Alias match
        alias_map = {}
        for name, ref in merged.items():
            for alias in ref.aliases:
                alias_map[alias] = name

        changed = True
        while changed:
            changed = False
            for entry in all_entries:
                name = entry.get("name", "")
                if name not in merged:
                    # Check if this name is an alias of an existing character
                    if name in alias_map:
                        target = alias_map[name]
                        self._merge_fields(merged[target], _to_char_ref(entry, id_counter))
                        id_counter += 1
                        # Add the name as an alias
                        if name not in merged[target].aliases:
                            merged[target].aliases.append(name)
                        # Remove the duplicate entry
                        changed = True

        # Step 3: Fuzzy match (edit distance <= 2 for Chinese)
        unmatched = [n for n in merged.keys() if False]  # Placeholder, users confirm via UI
        # Fuzzy match is handled at the UI layer; local assembler only does exact+alias

        return list(merged.values())

    def _merge_fields(self, target: CharacterRef, source: CharacterRef):
        """Merge source into target, keeping target's values as authoritative."""
        if source.personality and not target.personality:
            target.personality = source.personality
        if source.background and not target.background:
            target.background = source.background
        if source.age and not target.age:
            target.age = source.age
        if source.gender and not target.gender:
            target.gender = source.gender
        if source.role and not target.role:
            target.role = source.role
        for alias in source.aliases:
            if alias not in target.aliases:
                target.aliases.append(alias)

    def _parse_scenes(self, yaml_text: str, chapter_index: int,
                      context: ContextHub) -> List[Scene]:
        """Parse scene blocks from a chapter's YAML output."""
        scenes = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data:
                return scenes

            # The AI may output {"scenes": [...]} or {"screenplay": {"scenes": [...]}}
            scenes_data = data.get("scenes", [])
            if not scenes_data and "screenplay" in data:
                scenes_data = data["screenplay"].get("scenes", [])
            if not scenes_data:
                return scenes

            for i, s in enumerate(scenes_data, 1):
                heading = s.get("heading", "")
                location = s.get("location", "")
                interior = s.get("interior", True)
                if isinstance(interior, str):
                    interior = interior.lower() in ("true", "是", "内", "内景")

                scene = Scene(
                    id=f"scene_tmp_{chapter_index}_{i}",
                    number=i,
                    heading=heading,
                    location=location or heading.replace("【内】", "").replace("【外】", "").split("·")[0].strip(),
                    time=s.get("time", "日"),
                    interior=interior,
                    summary=s.get("summary", ""),
                    content=self._parse_content(s.get("content", [])),
                    chapter_index=chapter_index,
                )
                scenes.append(scene)
        except yaml.YAMLError:
            pass
        return scenes

    def _parse_content(self, content_list: List[dict]) -> List[ContentBlock]:
        blocks = []
        for c in content_list:
            blocks.append(ContentBlock(
                type=c.get("type", "action"),
                description=c.get("description"),
                character_id=c.get("character_id"),
                line=c.get("line"),
                delivery=c.get("delivery"),
                transition_type=c.get("transition_type"),
            ))
        return blocks

    def _build_acts(self, scenes: List[Scene], novel: NovelInput) -> List[Act]:
        acts = []
        for ch in novel.chapters:
            ch_scenes = [s for s in scenes if s.chapter_index == ch.index]
            if ch_scenes:
                acts.append(Act(
                    id=f"act_{ch.index}",
                    title=f"第{ch.index}章",
                    summary=ch.title or f"第{ch.index}章",
                    scenes=ch_scenes,
                ))
            else:
                acts.append(Act(
                    id=f"act_{ch.index}",
                    title=f"第{ch.index}章",
                    summary=f"第{ch.index}章",
                ))
        return acts

    # ---- Continuity checks ----

    def _check_orphan_characters(self, scenes: List[Scene],
                                  characters: List[CharacterRef]) -> List[ContinuityWarning]:
        warnings = []
        char_ids = {c.id for c in characters}
        for scene in scenes:
            for block in scene.content:
                if block.character_id and block.character_id not in char_ids:
                    warnings.append(ContinuityWarning(
                        level="warning",
                        type="orphan_character",
                        message=f"角色 {block.character_id} 在场景 {scene.heading} 中出现，但未在角色表中定义",
                        locations=[scene.id],
                    ))
        return warnings

    def _check_location_consistency(self, scenes: List[Scene]) -> List[ContinuityWarning]:
        warnings = []
        location_interiors: Dict[str, bool] = {}
        for scene in scenes:
            loc = scene.location
            if loc in location_interiors:
                if location_interiors[loc] != scene.interior:
                    warnings.append(ContinuityWarning(
                        level="warning",
                        type="inconsistent_location",
                        message=f"场景「{loc}」在前的内外景标志不一致（之前：{'内景' if location_interiors[loc] else '外景'}，本场：{'内景' if scene.interior else '外景'}）",
                        locations=[scene.id],
                    ))
            else:
                location_interiors[loc] = scene.interior
        return warnings

    def _check_scene_gaps(self, scenes: List[Scene]) -> List[ContinuityWarning]:
        warnings = []
        for i, scene in enumerate(scenes):
            if i > 0:
                prev = scenes[i - 1]
                has_transition = any(b.type == "transition" for b in prev.content)
                if not has_transition and scene.chapter_index == prev.chapter_index:
                    warnings.append(ContinuityWarning(
                        level="info",
                        type="missing_transition",
                        message=f"场景「{scene.heading}」与前一场景之间缺少转场标记",
                        locations=[scene.id],
                    ))
        return warnings

    def _check_character_descriptions(self, chapter_yamls: Dict[int, str],
                                       context: ContextHub) -> List[ContinuityWarning]:
        warnings = []
        char_traits: Dict[str, List[Tuple[int, str]]] = {}

        for ch_idx, yaml_text in chapter_yamls.items():
            try:
                data = yaml.safe_load(yaml_text)
                if data and "characters" in data:
                    for c in data["characters"]:
                        name = c.get("name", "")
                        personality = c.get("personality")
                        background = c.get("background")
                        if name and personality:
                            if name not in char_traits:
                                char_traits[name] = []
                            char_traits[name].append((ch_idx, personality))
            except yaml.YAMLError:
                pass

        for name, traits in char_traits.items():
            if len(traits) > 1:
                first_val = traits[0][1]
                for ch_idx, val in traits[1:]:
                    if val and val != first_val:
                        warnings.append(ContinuityWarning(
                            level="warning",
                            type="character_description_changed",
                            message=f"角色「{name}」的性格描述在第{traits[0][0]}章和第{ch_idx}章中存在不一致：\"{first_val}\" vs \"{val}\"",
                            locations=[],
                        ))
        return warnings


def _to_char_ref(d: dict, default_id_suffix: int = 0) -> CharacterRef:
    """Convert a dict to CharacterRef. If default_id_suffix is provided, generate a unique ID."""
    char_id = d.get("id")
    if not char_id:
        char_id = f"char_{default_id_suffix:03d}" if default_id_suffix else "char_999"
    return CharacterRef(
        id=char_id,
        name=d.get("name", "未知"),
        aliases=d.get("aliases") or [],
        role=d.get("role"),
        gender=d.get("gender"),
        age=d.get("age"),
        personality=d.get("personality"),
        background=d.get("background"),
        notes=d.get("notes"),
    )
