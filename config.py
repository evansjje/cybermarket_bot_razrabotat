from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = [0]

settings = Settings()
