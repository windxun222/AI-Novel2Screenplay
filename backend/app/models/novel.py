from pydantic import BaseModel, Field
from typing import List, Optional


class ParseRequest(BaseModel):
    text: str
    title: Optional[str] = "未命名作品"
    author: Optional[str] = ""


class ChapterInput(BaseModel):
    index: int = Field(ge=1)
    title: Optional[str] = None
    text: str


class NovelInput(BaseModel):
    title: str
    author: Optional[str] = None
    chapters: List[ChapterInput] = Field(min_length=1)
