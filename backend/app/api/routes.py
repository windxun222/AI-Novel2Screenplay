from fastapi import APIRouter, HTTPException, Body
from typing import List

from app.models.novel import NovelInput, ChapterInput
from app.models.screenplay import Screenplay
from app.services.ai_service import AIService
from app.services.converter import Converter
from app.services.parser import split_chapters
import yaml

router = APIRouter(prefix="/api", tags=["conversion"])


@router.post("/chapters/parse")
async def parse_chapters(text: str = Body(...), title: str = Body("未命名作品"), author: str = Body("")):
    """Parse raw novel text into chapters (local processing, no API)."""
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
        raise HTTPException(status_code=400, detail="章节解析失败：%s" % str(e))


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
        raise HTTPException(status_code=500, detail="转换过程出错：%s" % str(e))


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
                    "chapter_count": "int >= 3 章节数",
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
