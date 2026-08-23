from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: list[int] = []

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @field_validator('ADMIN_IDS', mode='before')
    def parse_admin_ids(cls, v):
        if isinstance(v, (int, str)):
            return [int(x.strip()) for x in str(v).replace('[', '').replace(']', '').replace('"', '').split(',') if x.strip().isdigit()]
        return v


settings = Settings()
