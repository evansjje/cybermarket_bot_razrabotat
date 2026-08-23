from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Union, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    YOOKASSA_SHOP_ID: str = "YOUR_SHOP_ID_HERE"
    YOOKASSA_SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    YOOKASSA_PAYMENT_TOKEN: str = "YOUR_PAYMENT_TOKEN_HERE"  # для Telegram Payments
    ADMIN_IDS: Union[List[int], str] = [123456789]  # ID администраторов

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            # Парсим строку вида "123,456,789" или "[123, 456]"
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                v = v[1:-1]
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        if not v or v == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("BOT_TOKEN не может быть пустым. Укажите токен бота в .env файле")
        return v

    @property
    def admin_ids_list(self) -> List[int]:
        """Возвращает список ID администраторов"""
        if isinstance(self.ADMIN_IDS, list):
            return self.ADMIN_IDS
        return [int(x) for x in str(self.ADMIN_IDS).split(",") if x.strip().isdigit()]

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in self.admin_ids_list


settings = Settings()
