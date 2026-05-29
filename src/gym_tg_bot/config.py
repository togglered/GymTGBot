from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    qdrant_path: Path = Path("./data/qdrant")

    bot_token: SecretStr
    openai_api_key: SecretStr
    openai_model: str = "gpt-4o-mini"
    log_level: str = "INFO"
