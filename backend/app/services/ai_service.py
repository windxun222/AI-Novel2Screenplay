from openai import OpenAI, APIError
from typing import Optional

from app.config import settings


class AIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.deepseek_api_key or "sk-placeholder",
            base_url=settings.deepseek_base_url,
        )
        self.model = settings.deepseek_model

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.3, max_tokens: int = 4096) -> Optional[str]:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except APIError as e:
            raise RuntimeError(f"DeepSeek API error: {e}") from e

    def is_available(self) -> bool:
        return bool(settings.deepseek_api_key)
