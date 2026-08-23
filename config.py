# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: SecretStr
    ADMIN_ID: int = 123456789  # безопасный дефолт

    @property
    def bot_token(self) -> str:
        return self.bot_token_value()

    def bot_token_value(self) -> str:
        return self.BOT_TOKEN.get_secret_value()


settings = Settings()
