from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    deepseek_api_key: str = ''
    deepseek_base_url: str = 'https://api.deepseek.com'
    deepseek_model: str = 'deepseek-chat'
    max_chapter_chars: int = 8000
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    cors_origins: str = 'http://localhost:5173,http://localhost:3000'

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8'}


settings = Settings()
