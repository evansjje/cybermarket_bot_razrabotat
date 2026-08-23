from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Union, List


class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    YOOKASSA_SHOP_ID: str = "YOUR_SHOP_ID"
    YOOKASSA_SECRET_KEY: str = "YOUR_SECRET_KEY"
    ADMIN_IDS: Union[List[int], str] = "123456789"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v


settings = Settings()
