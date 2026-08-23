from typing import Union, List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    YOOKASSA_SHOP_ID: str = "YOUR_SHOP_ID"
    YOOKASSA_SECRET_KEY: str = "YOUR_SECRET_KEY"
    ADMIN_IDS: Union[List[int], str, int] = []

    @field_validator('ADMIN_IDS', mode='before')
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(',') if x.strip().isdigit()]
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(x) for x in v if isinstance(x, (int, str)) and str(x).isdigit()]
        return []

    @property
    def admin_ids_list(self) -> List[int]:
        if isinstance(self.ADMIN_IDS, list):
            return self.ADMIN_IDS
        if isinstance(self.ADMIN_IDS, int):
            return [self.ADMIN_IDS]
        return []


settings = Settings()
