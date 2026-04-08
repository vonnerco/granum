from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Granum AI Text Enhancement API'
    app_version: str = '1.0.0'
    environment: str = Field(default='development')

    host: str = Field(default='0.0.0.0')
    port: int = Field(default=8000)

    database_url: str = Field(default='sqlite+aiosqlite:///data/text_enhancer.db')

    google_generative_ai_api_key: str | None = None
    llm_model: str = Field(default='gemini-2.5-flash-lite')


@lru_cache
def get_settings() -> Settings:
    return Settings()
