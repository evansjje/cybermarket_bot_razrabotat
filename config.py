from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    YOOKASSA_SHOP_ID: str = "YOUR_SHOP_ID"
    YOOKASSA_SECRET_KEY: str = "YOUR_SECRET_KEY"
    ADMIN_IDS: List[int] = [123456789]  # Default admin ID

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            # Parse string like "123,456,789" or "[123,456]"
            v = v.strip("[]").replace(" ", "")
            if v:
                return [int(x) for x in v.split(",") if x]
            return []
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(x) for x in v]
        return []

    @property
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.ADMIN_IDS


settings = Settings()
