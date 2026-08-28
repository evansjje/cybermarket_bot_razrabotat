# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = []

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        env_file_encoding='utf-8'
    )

    @field_validator('ADMIN_IDS', mode='before')
    def parse_admin_ids(cls, v):
        if isinstance(v, (int, str)):
            return [int(x.strip()) for x in str(v).replace('[', '').replace(']', '').replace('"', '').split(',') if x.strip().isdigit()]
        return v


settings = Settings()
