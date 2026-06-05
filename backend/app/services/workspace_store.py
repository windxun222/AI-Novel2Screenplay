import json
import logging
from pathlib import Path
from typing import List, Optional

from app.models.workspace import Workspace, WorkspaceSummary

logger = logging.getLogger("workspace_store")

WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "workspaces"


def _ensure_dir() -> None:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def _file_path(workspace_id: str) -> Path:
    # Sanitize to prevent path traversal
    safe_id = Path(workspace_id).name
    return WORKSPACE_DIR / f"{safe_id}.json"


def list_all() -> List[WorkspaceSummary]:
    """Return summaries for all saved workspaces, newest first."""
    _ensure_dir()
    results: List[WorkspaceSummary] = []
    for fpath in sorted(WORKSPACE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            results.append(WorkspaceSummary(**data))
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Skipping corrupt workspace file %s: %s", fpath.name, e)
    return results


def load(workspace_id: str) -> Optional[Workspace]:
    """Load a full workspace by ID."""
    fpath = _file_path(workspace_id)
    if not fpath.exists():
        return None
    try:
        return Workspace(**json.loads(fpath.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Cannot load workspace %s: %s", workspace_id, e)
        return None


def save(workspace: Workspace) -> Workspace:
    """Persist workspace to disk. Creates or overwrites."""
    _ensure_dir()
    # Bump updated_at
    from app.models.workspace import _now
    workspace.updated_at = _now()
    fpath = _file_path(workspace.id)
    fpath.write_text(workspace.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    return workspace


def delete(workspace_id: str) -> bool:
    """Delete a workspace file. Returns True if file was removed."""
    fpath = _file_path(workspace_id)
    if fpath.exists():
        fpath.unlink()
        return True
    return False
