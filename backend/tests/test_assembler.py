"""Tests for the assembler (character merging, scene assembly, continuity)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.novel import NovelInput, ChapterInput
from app.models.screenplay import Scene, ContentBlock, CharacterRef, ContinuityWarning
from app.services.assembler import Assembler, _to_char_ref
from app.services.converter import ContextHub


class TestCharacterMerge:
    def setup_method(self):
        self.assembler = Assembler()

    def test_merge_exact_name_match(self):
        chapter_yamls = {
            1: """
characters:
  - id: char_001
    name: Lin Mo
    personality: quiet
scenes: []
""",
            2: """
characters:
  - id: char_001
    name: Lin Mo
    personality: quiet
scenes: []
""",
        }
        context = ContextHub()
        chars = self.assembler._merge_characters(chapter_yamls, context)
        assert len(chars) == 1
        assert chars[0].name == "Lin Mo"

    def test_merge_different_chars(self):
        chapter_yamls = {
            1: """
characters:
  - id: char_001
    name: Lin Mo
scenes: []
""",
            2: """
characters:
  - id: char_002
    name: Su Wan
scenes: []
""",
        }
        context = ContextHub()
        chars = self.assembler._merge_characters(chapter_yamls, context)
        assert len(chars) == 2

    def test_alias_merge(self):
        chapter_yamls = {
            1: """
characters:
  - id: char_001
    name: Lin Mo
    aliases: [A Mo]
scenes: []
""",
            2: """
characters:
  - id: char_003
    name: A Mo
scenes: []
""",
        }
        context = ContextHub()
        chars = self.assembler._merge_characters(chapter_yamls, context)
        names = [c.name for c in chars]
        assert "Lin Mo" in names
        linmo = [c for c in chars if c.name == "Lin Mo"][0]
        assert "A Mo" in linmo.aliases


class TestSceneAssembly:
    def setup_method(self):
        self.assembler = Assembler()

    def test_scene_renumbering(self):
        yaml1 = """
scenes:
  - number: 1
    heading: outdoor
    location: street
    time: day
    interior: false
    summary: scene 1
    content: []
characters: []
"""
        yaml2 = """
scenes:
  - number: 1
    heading: indoor
    location: shop
    time: day
    interior: true
    summary: scene 2
    content: []
characters: []
"""
        context = ContextHub()
        scenes = self.assembler._parse_scenes(yaml1, 1, context)
        scenes2 = self.assembler._parse_scenes(yaml2, 2, context)
        assert len(scenes) == 1
        assert len(scenes2) == 1

    def test_scene_content_parsing(self):
        yaml_text = """
scenes:
  - number: 1
    heading: indoor scene
    location: tea house
    time: day
    interior: true
    summary: character enters
    content:
      - type: action
        description: Lin Mo walks in
      - type: dialogue
        character_id: char_001
        line: Hello again
        delivery: quietly
      - type: transition
        description: cut to
characters: []
"""
        context = ContextHub()
        scenes = self.assembler._parse_scenes(yaml_text, 1, context)
        assert len(scenes) == 1
        assert len(scenes[0].content) == 3
        assert scenes[0].content[0].type == "action"
        assert scenes[0].content[1].type == "dialogue"
        assert scenes[0].content[1].line == "Hello again"
        assert scenes[0].content[2].type == "transition"


class TestContinuityChecks:
    def setup_method(self):
        self.assembler = Assembler()

    def test_orphan_character_check(self):
        scenes = [
            Scene(
                id="scene_001", number=1, heading="test",
                location="somewhere", time="day", interior=True,
                content=[ContentBlock(type="dialogue", character_id="char_999", line="hello")],
                chapter_index=1,
            )
        ]
        chars = [CharacterRef(id="char_001", name="Lin Mo")]
        warnings = self.assembler._check_orphan_characters(scenes, chars)
        assert len(warnings) == 1
        assert warnings[0].type == "orphan_character"

    def test_no_orphan_when_character_exists(self):
        scenes = [
            Scene(
                id="scene_001", number=1, heading="test",
                location="somewhere", time="day", interior=True,
                content=[ContentBlock(type="dialogue", character_id="char_001", line="hello")],
                chapter_index=1,
            )
        ]
        chars = [CharacterRef(id="char_001", name="Lin Mo")]
        warnings = self.assembler._check_orphan_characters(scenes, chars)
        assert len(warnings) == 0

    def test_location_consistency(self):
        scenes = [
            Scene(id="scene_001", number=1, heading="outdoor",
                  location="street", time="day", interior=False, chapter_index=1),
            Scene(id="scene_002", number=2, heading="indoor",
                  location="street", time="day", interior=True, chapter_index=1),
        ]
        warnings = self.assembler._check_location_consistency(scenes)
        assert len(warnings) == 1
        assert warnings[0].type == "inconsistent_location"

    def test_scene_gap_check(self):
        scenes = [
            Scene(id="scene_001", number=1, heading="scene 1",
                  location="A", time="day", interior=True,
                  content=[ContentBlock(type="action", description="action")],
                  chapter_index=1),
            Scene(id="scene_002", number=2, heading="scene 2",
                  location="B", time="day", interior=True,
                  content=[ContentBlock(type="action", description="action")],
                  chapter_index=1),
        ]
        warnings = self.assembler._check_scene_gaps(scenes)
        assert len(warnings) == 1

    def test_no_gap_with_transition(self):
        scenes = [
            Scene(id="scene_001", number=1, heading="scene 1",
                  location="A", time="day", interior=True,
                  content=[ContentBlock(type="action", description="action"),
                           ContentBlock(type="transition", description="cut to")],
                  chapter_index=1),
            Scene(id="scene_002", number=2, heading="scene 2",
                  location="B", time="day", interior=True,
                  content=[ContentBlock(type="action", description="action")],
                  chapter_index=1),
        ]
        warnings = self.assembler._check_scene_gaps(scenes)
        assert len(warnings) == 0
