from pydantic import BaseModel, Field
from typing import List, Optional


class ChapterInput(BaseModel):
    index: int = Field(ge=1)
    title: Optional[str] = None
    text: str


class NovelInput(BaseModel):
    title: str
    author: Optional[str] = None
    chapters: List[ChapterInput] = Field(min_length=3)
