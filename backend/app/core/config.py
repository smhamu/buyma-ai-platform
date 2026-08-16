import os
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> str:
    app_env = os.getenv("APP_ENV", "development")
    return f".env.{app_env}"


class Settings(BaseSettings):
    app_env: Literal["development", "test", "production"] = "development"
    database_url: str
    secret_key: str
    algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    openai_api_key: str | None = None
    openai_chat_model: str | None = None
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    embedding_job_stale_minutes: int = 10
    embedding_recovery_batch_size: int = 100
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20
    registration_enabled: bool = True
    enable_api_docs: bool = True
    notification_outbox_consumer_enabled: bool = False
    notification_outbox_adapter: Literal["disabled", "noop"] = "disabled"
    notification_outbox_batch_size: int = 50
    notification_outbox_max_attempts: int = 5
    notification_outbox_base_backoff_seconds: int = 60
    notification_outbox_max_backoff_seconds: int = 3600
    notification_outbox_lease_seconds: int = 300
    
    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.app_env != "production":
            return self

        if len(self.secret_key) < 32 or self.secret_key.lower().startswith("change_me"):
            raise ValueError("Production SECRET_KEY must be a unique value of at least 32 characters.")
        if self.database_echo:
            raise ValueError("DATABASE_ECHO must be false in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
