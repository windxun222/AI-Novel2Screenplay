import re
from typing import List


def _is_chapter_heading(line: str) -> bool:
    """Check if a line looks like a chapter heading."""
    line = line.strip()
    patterns = [
        r"^第[零一二三四五六七八九十百千\d]+[章回节]",
        r"^第\d+章",
        r"^Chapter\s+\d+",
        r"^CHAPTER\s+\d+",
    ]
    return any(re.match(p, line) for p in patterns)


def split_chapters(text: str) -> List[str]:
    """Split novel text into chapters by line-by-line detection."""
    if not text.strip():
        return []

    lines = text.split("\n")
    chapter_lines: List[int] = []

    for i, line in enumerate(lines):
        if _is_chapter_heading(line):
            chapter_lines.append(i)

    if len(chapter_lines) < 2:
        return _fallback_split(text)

    chapters = []
    for idx in range(len(chapter_lines)):
        start = chapter_lines[idx]
        end = chapter_lines[idx + 1] if idx + 1 < len(chapter_lines) else len(lines)
        chunk = "\n".join(lines[start:end]).strip()
        if chunk:
            chapters.append(chunk)

    return chapters if chapters else _fallback_split(text)


def _fallback_split(text: str) -> List[str]:
    """Fallback: split by double newlines if no chapter markers found."""
    blocks = re.split(r"\n{3,}", text.strip())
    return [b for b in blocks if len(b.strip()) > 20]


def estimate_token_count(text: str) -> int:
    """Rough Chinese token estimation: ~1.5-2 tokens per character."""
    return int(len(text) * 1.8)


def needs_chunking(text: str, max_chars: int = 8000) -> bool:
    """Check if a chapter needs to be split into segments."""
    return len(text) > max_chars


def chunk_chapter(text: str, max_chars: int = 8000) -> List[str]:
    """Split an oversized chapter into smaller segments by paragraph breaks."""
    paragraphs = text.split("\n\n")
    segments = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > max_chars and current:
            segments.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(para)
        current_len += para_len

    if current:
        segments.append("\n\n".join(current))
    return segments if segments else [text]
