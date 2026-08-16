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
