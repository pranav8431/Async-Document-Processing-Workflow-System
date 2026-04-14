from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Async Document Processing Workflow"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/docflow"
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: str = "./uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
