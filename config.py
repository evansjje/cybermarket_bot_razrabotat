from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram bot token")
    ADMIN_IDS: List[int] = Field(default_factory=list, description="List of admin user IDs")
    DATABASE_PATH: str = Field(default="cybermarket.db", description="Path to SQLite database file")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            # Support comma-separated or space-separated values
            parts = v.replace(";", ",").replace(" ", ",").split(",")
            return [int(p.strip()) for p in parts if p.strip().isdigit()]
        if isinstance(v, (list, tuple, set)):
            return [int(x) for x in v if str(x).strip().isdigit()]
        return []

    @field_validator("BOT_TOKEN", mode="before")
    @classmethod
    def validate_bot_token(cls, v):
        if not v or not isinstance(v, str) or len(v) < 10:
            raise ValueError("BOT_TOKEN must be a valid non-empty string")
        return v.strip()


settings = Settings()
