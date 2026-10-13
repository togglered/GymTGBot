from pathlib import Path

import pytest
from pydantic import ValidationError

from gym_tg_bot.config import Settings


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("ALLOWED_CHANNEL_ID", "-1001111111111")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "-1002222222222")
    monkeypatch.setenv("ALLOWED_USER_ID", "42")


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    _set_required_env(monkeypatch)

    settings = Settings()  # type: ignore[call-arg]

    assert settings.bot_token.get_secret_value() == "test_token_123"
    assert settings.openai_api_key.get_secret_value() == "test_openai_key"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.log_level == "INFO"
    assert settings.allowed_channel_id == -1001111111111
    assert settings.allowed_chat_id == -1002222222222
    assert settings.allowed_user_id == 42


def test_settings_fails_without_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


@pytest.mark.parametrize("name", ["ALLOWED_CHANNEL_ID", "ALLOWED_CHAT_ID", "ALLOWED_USER_ID"])
def test_settings_fails_without_access_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    name: str,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]
