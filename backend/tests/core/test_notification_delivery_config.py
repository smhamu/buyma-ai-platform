import pytest
from pydantic import ValidationError

from app.core.config import Settings


def settings(**values):
    return Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@postgres/db",
        secret_key="x" * 40,
        **values,
    )


def test_disabled_delivery_is_valid():
    assert settings(notification_delivery_provider="disabled").notification_delivery_provider == "disabled"


def test_slack_requires_webhook():
    with pytest.raises(ValidationError, match="SLACK_WEBHOOK_URL"):
        settings(notification_delivery_provider="slack")


def test_production_rejects_noop_and_accepts_configured_slack():
    with pytest.raises(ValidationError, match="noop"):
        settings(app_env="production", notification_delivery_provider="noop")
    configured = settings(
        app_env="production", notification_delivery_provider="slack",
        slack_webhook_url="https://hooks.slack.com/services/a/b/c", database_echo=False,
        notification_secret_store="ssm",
    )
    assert configured.notification_delivery_provider == "slack"


@pytest.mark.parametrize("secret_store", ["memory", "redis"])
def test_production_rejects_non_ssm_secret_stores(secret_store):
    with pytest.raises(ValidationError, match="must use the SSM"):
        settings(app_env="production", notification_secret_store=secret_store)


def test_development_accepts_redis_and_test_accepts_memory():
    assert settings(app_env="development", notification_secret_store="redis").notification_secret_store == "redis"
    assert settings(app_env="test", notification_secret_store="memory").notification_secret_store == "memory"


def test_production_accepts_ssm_secret_store():
    assert settings(app_env="production", notification_secret_store="ssm").notification_secret_store == "ssm"
