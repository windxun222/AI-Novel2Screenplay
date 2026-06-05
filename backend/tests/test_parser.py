"""Tests for the chapter parser service."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.parser import split_chapters, estimate_token_count, needs_chunking, chunk_chapter


class TestSplitChapters:
    def test_chinese_numbered_chapters(self):
        text = (
            "第一章 开头\n这是第一章的内容。\n\n"
            "第二章 发展\n这是第二章的内容。\n\n"
            "第三章 结尾\n这是第三章的内容。"
        )
        result = split_chapters(text)
        assert len(result) == 3
        assert "第一章" in result[0]
        assert "第二章" in result[1]
        assert "第三章" in result[2]

    def test_arabic_numbered_chapters(self):
        text = "第1章 开始\n内容1\n\n第2章 继续\n内容2\n\n第3章 结束\n内容3"
        result = split_chapters(text)
        assert len(result) == 3

    def test_english_chapter_markers(self):
        text = "Chapter 1\nContent one.\n\nChapter 2\nContent two.\n\nChapter 3\nContent three."
        result = split_chapters(text)
        assert len(result) == 3

    def test_fallback_on_no_markers(self):
        text = "This is the first paragraph.\n\n\nThis is the second paragraph.\n\n\nThis is the third paragraph."
        result = split_chapters(text)
        assert len(result) >= 1

    def test_empty_text(self):
        assert split_chapters("") == []

    def test_less_than_3_chapters(self):
        text = "第一章\n内容\n\n第二章\n内容"
        result = split_chapters(text)
        assert len(result) >= 1


class TestTokenizer:
    def test_zero_text(self):
        assert estimate_token_count("") == 0

    def test_ascii_text(self):
        count = estimate_token_count("hello world")
        assert count == int(len("hello world") * 1.8)


class TestChunking:
    def test_small_text_no_chunking(self):
        assert needs_chunking("short text", 100) is False

    def test_large_text_needs_chunking(self):
        assert needs_chunking("x" * 200, 100) is True

    def test_chunk_chapter(self):
        text = "Para one.\n\nPara two.\n\nPara three.\n\nPara four."
        chunks = chunk_chapter(text, max_chars=10)
        assert len(chunks) >= 2
