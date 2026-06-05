from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import APP_VERSION
from app.config import settings
from app.api.routes import router

app = FastAPI(
    title="AI Novel2Screenplay",
    description="AI 小说转剧本工具 — 将小说自动转换为结构化剧本 YAML",
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"app": "AI Novel2Screenplay", "version": APP_VERSION, "status": "running"}
