from pathlib import Path

import pytest
from pydantic import ValidationError

from gym_tg_bot.config import Settings


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")

    settings = Settings()  # type: ignore[call-arg]

    assert settings.bot_token.get_secret_value() == "test_token_123"
    assert settings.openai_api_key.get_secret_value() == "test_openai_key"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.log_level == "INFO"


def test_settings_fails_without_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_reasoning_effort_defaults_to_none(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.delenv("OPENAI_REASONING_EFFORT", raising=False)

    settings = Settings()  # type: ignore[call-arg]

    assert settings.openai_reasoning_effort is None


def test_reasoning_effort_loads_from_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "none")

    settings = Settings()  # type: ignore[call-arg]

    assert settings.openai_reasoning_effort == "none"
