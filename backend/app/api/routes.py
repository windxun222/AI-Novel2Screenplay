from fastapi import APIRouter, HTTPException, Response
from typing import List, Dict
from pydantic import BaseModel

from app.models.novel import NovelInput, ChapterInput, ParseRequest
from app.models.screenplay import Screenplay
from app.models.workspace import Workspace, WorkspaceSummary
from app.services.ai_service import AIService
from app.services.converter import Converter
from app.services.workspace_store import list_all, load as load_ws, save as save_ws, delete as delete_ws
from app.services.parser import split_chapters
import yaml
from app.services.converter import _extract_yaml_block

router = APIRouter(prefix="/api", tags=["conversion"])


@router.post("/chapters/parse")
async def parse_chapters(req: ParseRequest):
    """Parse raw novel text into chapters (local processing, no API)."""
    text, title, author = req.text, req.title, req.author
    try:
        chapters_raw = split_chapters(text)
        result = []
        for i, ch_text in enumerate(chapters_raw, 1):
            lines = ch_text.strip().split("\n", 1)
            ch_title = lines[0].strip() if len(lines) > 1 else f"第{i}章"
            body = lines[1] if len(lines) > 1 else ch_text
            result.append({
                "index": i,
                "title": ch_title,
                "text": body,
                "text_preview": body[:200],
                "text_length": len(body),
            })
        return {"title": title, "author": author, "chapters": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"章节解析失败：{e}")


def _screenplay_to_yaml(screenplay: Screenplay) -> str:
    """Convert a Screenplay model to YAML string."""
    import datetime as dt
    # Build the dict manually for clean YAML structure
    doc = {
        "screenplay": {
            "metadata": {
                "title": screenplay.metadata.title,
                "source": screenplay.metadata.source,
                "author": screenplay.metadata.author,
                "adapter": screenplay.metadata.adapter,
                "created_at": screenplay.metadata.created_at.isoformat() if screenplay.metadata.created_at else str(dt.date.today()),
                "chapter_count": screenplay.metadata.chapter_count,
                "version": screenplay.metadata.version,
            },
            "characters": [],
            "acts": [],
            "warnings": [],
        }
    }
    for c in screenplay.characters:
        entry = {
            "id": c.id,
            "name": c.name,
            "aliases": c.aliases or [],
            "role": c.role,
            "gender": c.gender,
            "age": c.age,
            "personality": c.personality,
            "background": c.background,
            "notes": c.notes,
        }
        doc["screenplay"]["characters"].append({k: v for k, v in entry.items() if v is not None or k in ("id", "name", "aliases")})

    for act in screenplay.acts:
        act_entry = {
            "id": act.id,
            "title": act.title,
            "summary": act.summary,
            "scenes": [],
        }
        for scene in act.scenes:
            sc = {
                "id": scene.id,
                "number": scene.number,
                "heading": scene.heading,
                "location": scene.location,
                "time": scene.time,
                "interior": scene.interior,
                "summary": scene.summary,
                "chapter_index": scene.chapter_index,
                "content": [],
            }
            for block in scene.content:
                cb = {"type": block.type}
                if block.description:
                    cb["description"] = block.description
                if block.character_id:
                    cb["character_id"] = block.character_id
                if block.line:
                    cb["line"] = block.line
                if block.delivery:
                    cb["delivery"] = block.delivery
                if block.transition_type:
                    cb["transition_type"] = block.transition_type
                sc["content"].append(cb)
            act_entry["scenes"].append(sc)
        doc["screenplay"]["acts"].append(act_entry)

    for w in screenplay.warnings:
        doc["screenplay"]["warnings"].append({
            "level": w.level,
            "type": w.type,
            "message": w.message,
            "locations": w.locations or [],
        })

    return yaml.dump(doc, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)


@router.post("/convert/yaml")
async def convert_novel_yaml(novel: NovelInput):
    """Full pipeline, return YAML format screenplay."""
    ai = AIService()
    if not ai.is_available():
        raise HTTPException(
            status_code=503,
            detail="DeepSeek API 未配置。请在 .env 文件中设置 DEEPSEEK_API_KEY",
        )
    try:
        converter = Converter(ai)
        result = converter.convert(novel)
        if not result:
            raise HTTPException(status_code=500, detail="转换失败：未能生成剧本")
        yaml_str = _screenplay_to_yaml(result)
        return Response(content=yaml_str, media_type="text/yaml; charset=utf-8",
                        headers={"Content-Disposition": f"attachment; filename={novel.title or 'screenplay'}.yaml"})
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换过程出错：{e}")


@router.post("/convert", response_model=Screenplay)
async def convert_novel(novel: NovelInput):
    """Full pipeline: convert novel to screenplay via DeepSeek API."""
    ai = AIService()
    if not ai.is_available():
        raise HTTPException(
            status_code=503,
            detail="DeepSeek API 未配置。请在 .env 文件中设置 DEEPSEEK_API_KEY",
        )
    try:
        converter = Converter(ai)
        result = converter.convert(novel)
        if not result:
            raise HTTPException(status_code=500, detail="转换失败：未能生成剧本")
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换过程出错：{e}")



# ── Step-by-step conversion ──

class PreScanResult(BaseModel):
    characters: List[dict] = []
    chapter_summaries: Dict[int, str] = {}


class ChapterConvertRequest(BaseModel):
    chapter_index: int
    chapter_text: str
    existing_characters: List[dict] = []
    previous_summaries: Dict[int, str] = {}


@router.post("/convert/pre-scan")
async def pre_scan_novel(novel: NovelInput):
    """Phase 0 only: pre-scan to extract global character list and chapter summaries."""
    ai = AIService()
    if not ai.is_available():
        raise HTTPException(status_code=503, detail="DeepSeek API not configured")
    converter = Converter(ai)
    success = converter.pre_scan(novel)
    if not success:
        raise HTTPException(status_code=500, detail="Pre-scan failed")
    return {
        "characters": converter.context.characters,
        "chapter_summaries": converter.context.chapter_summaries,
    }


@router.post("/convert/chapter")
async def convert_single_chapter(req: ChapterConvertRequest):
    """Phase 1 for one chapter: convert with provided context, return YAML."""
    ai = AIService()
    if not ai.is_available():
        raise HTTPException(status_code=503, detail="DeepSeek API not configured")
    converter = Converter(ai)
    # Inject existing context
    converter.context.characters = req.existing_characters
    converter.context.chapter_summaries = req.previous_summaries
    # Convert the chapter
    ch = ChapterInput(index=req.chapter_index, text=req.chapter_text)
    raw = converter.convert_chapter(NovelInput(title="", chapters=[ch]), ch)
    if not raw:
        raise HTTPException(status_code=500, detail=f"Chapter {req.chapter_index} conversion failed")
    # Parse the YAML to extract scenes + new characters
    try:
        cleaned = _extract_yaml_block(raw)
        data = yaml.safe_load(cleaned)
        scenes_data = data.get("scenes", []) if data else []
        chars_data = data.get("characters", []) if data else []
    except Exception:
        scenes_data = []
        chars_data = []

    # Post-process: remap character_ids in scenes to match pre-scan IDs
    name_to_id = {}
    for ec in req.existing_characters:
        if ec.get("name") and ec.get("id"):
            name_to_id[ec["name"]] = ec["id"]
    ch_id_to_name = {}
    for cc in chars_data:
        if cc.get("id") and cc.get("name"):
            ch_id_to_name[cc["id"]] = cc["name"]
    for scene in scenes_data:
        for block in scene.get("content", []):
            if block.get("type") == "dialogue" and block.get("character_id"):
                cid = block["character_id"]
                if cid in ch_id_to_name:
                    ch_name = ch_id_to_name[cid]
                    if ch_name in name_to_id:
                        correct_id = name_to_id[ch_name]
                        if correct_id != cid:
                            block["character_id"] = correct_id

    return {
        "raw_yaml": raw,
        "scenes": scenes_data,
        "new_characters": chars_data,
    }



@router.post("/convert/recheck")
async def recheck_warnings(screenplay: Screenplay):
    """Re-run continuity checks on the current screenplay state."""
    from app.services.assembler import Assembler
    
    # Build a minimal context to run checks
    class CheckContext:
        def __init__(self):
            self.characters = []
            self.continuity_warnings = []
    
    assembler = Assembler()
    ctx = CheckContext()
    
    # Flatten all scenes
    all_scenes = []
    for act in screenplay.acts:
        for scene in act.scenes:
            all_scenes.append(scene)
    
    new_warnings = []
    
    # Run all checks
    for w in assembler._check_orphan_characters(all_scenes, screenplay.characters):
        new_warnings.append(w)
    for w in assembler._check_location_consistency(all_scenes):
        new_warnings.append(w)
    for w in assembler._check_scene_gaps(all_scenes):
        new_warnings.append(w)
    for w in ctx.continuity_warnings:
        new_warnings.append(w)
    
    return {"warnings": new_warnings}

class AssembleRequest(BaseModel):
    title: str = ""
    author: str = ""
    chapters: list = []
    characters: list = []


@router.post("/convert/assemble")
async def assemble_chapters(req: AssembleRequest):
    """Phase 2: assemble pre-collected chapter YAMLs with character context."""
    from app.services.assembler import Assembler
    from app.models.novel import NovelInput, ChapterInput
    chapter_yamls = {}
    novel_chapters = []
    for ch in req.chapters:
        idx = ch.get("index", 0)
        chapter_yamls[idx] = ch.get("text", "")
        novel_chapters.append(ChapterInput(index=idx, text=ch.get("text", ""), title=ch.get("title", "")))
    novel = NovelInput(title=req.title, author=req.author, chapters=novel_chapters)

    class StepContext:
        def __init__(self):
            self.characters = req.characters
            self.continuity_warnings = []
    ctx = StepContext()

    assembler = Assembler()
    result = assembler.assemble(novel, chapter_yamls, ctx)
    if not result:
        raise HTTPException(status_code=500, detail="Assembly failed")

    # Post-assembly: remap character_ids in all scenes to match pre-scan IDs
    name_to_id = {}
    for c in req.characters:
        if c.get("name") and c.get("id"):
            name_to_id[c["name"]] = c["id"]

    for act in result.acts:
        for scene in act.scenes:
            for block in scene.content:
                if block.character_id:
                    # Find which character this ID refers to (by ID match in result characters)
                    ref = next((rc for rc in result.characters if rc.id == block.character_id), None)
                    if ref and ref.name in name_to_id:
                        correct_id = name_to_id[ref.name]
                        if correct_id != block.character_id:
                            block.character_id = correct_id
    return result


@router.get("/schema")
async def get_schema():
    """Return the screenplay YAML schema as JSON."""
    return {
        "version": "1.0",
        "description": "AI Novel2Screenplay 剧本 YAML Schema",
        "schema": {
            "screenplay": {
                "metadata": {
                    "title": "string (必填) 剧本标题",
                    "source": "string (可选) 小说原名",
                    "author": "string (可选) 原著作者",
                    "adapter": "string AI Novel2Screenplay",
                    "created_at": "date 转换日期",
                    "chapter_count": "int >= 1 章节数",
                    "version": "string Schema版本"
                },
                "characters": [
                    {
                        "id": "string char_XXX",
                        "name": "string 角色姓名",
                        "aliases": ["string 别名"],
                        "role": "string 主角/配角/反派",
                        "gender": "string 男/女",
                        "age": "string 年龄",
                        "personality": "string 性格描述",
                        "background": "string 背景",
                        "notes": "string 备注"
                    }
                ],
                "acts": [
                    {
                        "id": "string act_X",
                        "title": "string",
                        "summary": "string",
                        "scenes": [
                            {
                                "id": "string scene_XXX",
                                "number": "int >= 1",
                                "heading": "string 【内|外】地点·时间",
                                "location": "string",
                                "time": "string 晨/日/黄昏/夜",
                                "interior": "bool",
                                "summary": "string",
                                "content": [
                                    {
                                        "type": "string action|dialogue|narration|transition",
                                        "description": "string (type=action|narration)",
                                        "character_id": "string (type=dialogue)",
                                        "line": "string (type=dialogue)",
                                        "delivery": "string (可选) 语气指示",
                                        "transition_type": "string (type=transition)"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "warnings": [
                    {
                        "level": "string info|warning|error",
                        "type": "string 警告类型",
                        "message": "string",
                        "locations": ["string 关联场景ID"]
                    }
                ]
            }
        }
    }


# ── Workspace CRUD ──

workspace_router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@workspace_router.get("", response_model=List[WorkspaceSummary])
async def list_workspaces():
    """List all saved workspaces (summary only)."""
    return list_all()


@workspace_router.post("", response_model=Workspace)
async def create_workspace(ws: Workspace):
    """Create or overwrite a workspace."""
    return save_ws(ws)


@workspace_router.get("/{workspace_id}", response_model=Workspace)
async def get_workspace(workspace_id: str):
    """Load a full workspace by ID."""
    ws = load_ws(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"工作区不存在：{workspace_id}")
    return ws


@workspace_router.put("/{workspace_id}", response_model=Workspace)
async def update_workspace(workspace_id: str, ws: Workspace):
    """Save/update a workspace."""
    # Ensure path ID matches body
    if ws.id != workspace_id:
        ws.id = workspace_id
    return save_ws(ws)


@workspace_router.delete("/{workspace_id}")
async def remove_workspace(workspace_id: str):
    """Delete a workspace."""
    if not delete_ws(workspace_id):
        raise HTTPException(status_code=404, detail=f"工作区不存在：{workspace_id}")
    return {"deleted": workspace_id}
