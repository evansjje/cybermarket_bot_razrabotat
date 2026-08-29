# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = []

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @field_validator('ADMIN_IDS', mode='before')
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(i.strip()) for i in v.split(',') if i.strip().isdigit()]
        return v


settings = Settings()
