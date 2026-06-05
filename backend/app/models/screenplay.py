from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date


ContentType = Literal['action', 'dialogue', 'narration', 'transition']


class CharacterRef(BaseModel):
    id: str = Field(pattern=r'^char_\d{3,}$')
    name: str
    aliases: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    notes: Optional[str] = None


class ContentBlock(BaseModel):
    type: ContentType
    description: Optional[str] = None
    character_id: Optional[str] = None
    line: Optional[str] = None
    delivery: Optional[str] = None
    transition_type: Optional[str] = None


class Scene(BaseModel):
    id: str = "scene_001"
    number: int = Field(ge=1)
    heading: str
    location: str
    time: str
    interior: bool = True
    summary: Optional[str] = None
    content: List[ContentBlock] = Field(default_factory=list)
    chapter_index: int = Field(ge=1)


class Act(BaseModel):
    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    scenes: List[Scene] = Field(default_factory=list)


class ContinuityWarning(BaseModel):
    level: Literal['info', 'warning', 'error']
    type: str
    message: str
    locations: List[str] = Field(default_factory=list)


class ScreenplayMeta(BaseModel):
    title: str
    source: Optional[str] = None
    author: Optional[str] = None
    adapter: str = 'AI Novel2Screenplay'
    created_at: date = Field(default_factory=date.today)
    chapter_count: int = Field(ge=1)
    version: str = '1.0'


class Screenplay(BaseModel):
    metadata: ScreenplayMeta
    characters: List[CharacterRef] = Field(default_factory=list)
    acts: List[Act] = Field(default_factory=list)
    warnings: List[ContinuityWarning] = Field(default_factory=list)
