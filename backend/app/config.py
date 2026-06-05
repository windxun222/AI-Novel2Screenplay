from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    deepseek_api_key: str = ''
    deepseek_base_url: str = 'https://api.deepseek.com'
    deepseek_model: str = 'deepseek-chat'
    max_chapter_chars: int = 8000
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    cors_origins: str = 'http://localhost:5173,http://localhost:3000'
    # AI 输出 token 上限（DeepSeek-chat 支持 8192）
    pre_scan_max_tokens: int = 4096
    chapter_max_tokens: int = 8192

    model_config = {
        'env_file': str(Path(__file__).resolve().parent.parent.parent / '.env'),
        'env_file_encoding': 'utf-8',
    }


settings = Settings()
