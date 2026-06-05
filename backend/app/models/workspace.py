from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any
from datetime import datetime, timezone
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


WorkspaceStatus = Literal["draft", "converting", "completed", "error"]


class WorkspaceSummary(BaseModel):
    """Lightweight workspace metadata returned by list endpoint."""
    id: str
    title: str
    author: Optional[str] = None
    chapter_count: int = 0
    status: WorkspaceStatus = "draft"
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class Workspace(BaseModel):
    """Full workspace payload for save / load."""
    id: str = Field(default_factory=_new_id)
    title: str = "未命名作品"
    author: Optional[str] = None
    status: WorkspaceStatus = "draft"
    raw_text: str = ""
    chapters: List[dict] = []
    screenplay: Optional[dict] = None
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)
