import re
from typing import List, Optional, Dict, Any
from app.config import settings
from app.models.novel import NovelInput, ChapterInput
from app.models.screenplay import Screenplay, ContinuityWarning
from app.services.parser import chunk_chapter, needs_chunking
from app.services.ai_service import AIService
from app.prompts.pre_scan import PRE_SCAN_SYSTEM_PROMPT, PRE_SCAN_USER_TEMPLATE
from app.prompts.system import SYSTEM_PROMPT, build_chapter_prompt
import yaml


class ContextHub:
    """Accumulates cross-chapter context during sequential conversion."""

    def __init__(self):
        self.characters: List[Dict[str, Any]] = []
        self.chapter_summaries: Dict[int, str] = {}
        self.chapter_yamls: Dict[int, str] = {}
        self.continuity_warnings: List[ContinuityWarning] = []

    def update_characters(self, chars_yaml: str, chapter_index: int):
        """Parse and merge characters from a chapter YAML output."""
        try:
            data = yaml.safe_load(chars_yaml)
            if not data or "characters" not in data:
                return
            for c in data["characters"]:
                existing = [x for x in self.characters if x.get("name") == c.get("name")]
                if not existing:
                    self.characters.append(c)
        except yaml.YAMLError:
            pass

    def get_character_context_yaml(self) -> str:
        """Serialize current character table to YAML string for prompt injection.
        Includes id if present, plus key fields to help AI match characters."""
        if not self.characters:
            return ""
        clean = []
        for c in self.characters:
            entry = {}
            if c.get("id"):
                entry["id"] = c["id"]
            entry["name"] = c.get("name", "")
            if c.get("aliases"):
                entry["aliases"] = c["aliases"]
            if c.get("role"):
                entry["role"] = c["role"]
            if c.get("personality"):
                entry["personality"] = c["personality"]
            clean.append(entry)
        return yaml.dump({"characters": clean}, allow_unicode=True, default_flow_style=False)

    def get_summary_context(self, up_to_chapter: int) -> str:
        """Build summary context string for prompt injection."""
        lines = []
        for idx in sorted(self.chapter_summaries):
            if idx < up_to_chapter:
                lines.append(f"第{idx}章概要：{self.chapter_summaries[idx]}")
        return "\n".join(lines)

    def add_warning(self, level: str, wtype: str, message: str, locations: List[str] = None):
        self.continuity_warnings.append(ContinuityWarning(
            level=level, type=wtype, message=message,
            locations=locations or []
        ))


class Converter:
    """Orchestrates the full novel-to-screenplay conversion pipeline."""

    def __init__(self, ai_service: AIService):
        self.ai = ai_service
        self.context = ContextHub()

    def pre_scan(self, novel: NovelInput) -> bool:
        """Phase 0: Lightweight pre-scan to extract character names and chapter summaries."""
        chapter_texts = "\n\n=====\n\n".join(
            f"第{c.index}章：{c.text}" for c in novel.chapters
        )
        user_msg = PRE_SCAN_USER_TEMPLATE.format(
            title=novel.title,
            author=novel.author or "未知",
            chapter_texts=chapter_texts,
        )
        raw = self.ai.chat(PRE_SCAN_SYSTEM_PROMPT, user_msg, temperature=0.1,
                           max_tokens=settings.pre_scan_max_tokens)
        if not raw:
            return False

        try:
            cleaned = _extract_yaml_block(raw)
            data = yaml.safe_load(cleaned)
            if data and "chapters" in data:
                for ch in data["chapters"]:
                    self.context.chapter_summaries[ch["index"]] = ch["summary"]
            if data and "characters" in data:
                for c in data["characters"]:
                    existing = [x for x in self.context.characters if x.get("name") == c.get("name")]
                    if not existing:
                        self.context.characters.append(c)
            # Assign stable IDs to all characters
            for idx, ch in enumerate(self.context.characters):
                if not ch.get("id"):
                    ch["id"] = f"char_{idx + 1:03d}"
            return True
        except yaml.YAMLError:
            return False

    def convert_chapter(self, novel: NovelInput, chapter: ChapterInput) -> Optional[str]:
        """Phase 1: Convert a single chapter with context injection."""
        char_ctx = self.context.get_character_context_yaml()
        summary_ctx = self.context.get_summary_context(chapter.index)

        user_prompt = build_chapter_prompt(chapter.index, chapter.text, char_ctx, summary_ctx)
        raw = self.ai.chat(SYSTEM_PROMPT, user_prompt, temperature=0.1,
                           max_tokens=settings.chapter_max_tokens)
        if not raw:
            return None

        cleaned = _extract_yaml_block(raw)
        self.context.update_characters(cleaned, chapter.index)

        try:
            data = yaml.safe_load(cleaned)
            if data and "chapters" not in data and "scenes" in data:
                pass
        except yaml.YAMLError:
            pass

        return cleaned

    def convert(self, novel: NovelInput) -> Optional[Screenplay]:
        """Run the full pipeline: pre-scan -> sequential chapter conversion -> assembly."""
        if not self.ai.is_available():
            raise RuntimeError("DeepSeek API key not configured. Set DEEPSEEK_API_KEY in .env")

        self.pre_scan(novel)
        chapter_yamls = {}

        for chapter in novel.chapters:
            text = chapter.text
            if needs_chunking(text, settings.max_chapter_chars):
                segments = chunk_chapter(text, settings.max_chapter_chars)
                seg_results = []
                for i, seg in enumerate(segments):
                    seg_ch = ChapterInput(index=chapter.index, title=chapter.title, text=seg)
                    result = self.convert_chapter(novel, seg_ch)
                    if result:
                        seg_results.append(result)
                if seg_results:
                    chapter_yamls[chapter.index] = "\n".join(seg_results)
            else:
                result = self.convert_chapter(novel, chapter)
                if result:
                    chapter_yamls[chapter.index] = result

        from app.services.assembler import Assembler
        assembler = Assembler()
        return assembler.assemble(novel, chapter_yamls, self.context)


def _sanitize_char_dict(c: dict):
    """Ensure string fields in a character dict are proper strings, not lists."""
    for field in ("role", "gender", "age", "personality", "background", "notes"):
        val = c.get(field)
        if val is not None and not isinstance(val, str):
            if isinstance(val, list):
                c[field] = ", ".join(str(x) for x in val if x) or ""
            else:
                c[field] = str(val) if val else ""
    if not isinstance(c.get("aliases"), list):
        c["aliases"] = []


def _extract_yaml_block(text: str) -> str:
    """Extract YAML content from a response that may contain markdown fences."""
    match = re.search(r"```(?:yaml)?\s*\n(.+?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
