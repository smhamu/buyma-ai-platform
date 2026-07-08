import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> str:
    app_env = os.getenv("APP_ENV", "development")
    return f".env.{app_env}"


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()