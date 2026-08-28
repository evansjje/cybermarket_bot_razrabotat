from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


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

    @field_validator('BOT_TOKEN')
    @classmethod
    def validate_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError('BOT_TOKEN is invalid')
        return v


settings = Settings()
