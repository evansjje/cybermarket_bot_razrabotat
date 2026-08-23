import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """Настройки бота через Pydantic Settings с безопасными дефолтами."""

    # Токен Telegram-бота
    BOT_TOKEN: SecretStr = SecretStr("YOUR_BOT_TOKEN_HERE")

    # ID администратора (число, можно несколько через запятую)
    ADMIN_IDS: list[int] = [123456789]

    # YooKassa (для тестовых платежей)
    YOOKASSA_SHOP_ID: str = "YOUR_SHOP_ID"
    YOOKASSA_SECRET_KEY: SecretStr = SecretStr("YOUR_SECRET_KEY")

    # Telegram Payments (альтернативный способ оплаты)
    TELEGRAM_PAYMENT_TOKEN: SecretStr = SecretStr("YOUR_TELEGRAM_PAYMENT_TOKEN")

    # Путь к файлу БД
    DATABASE_PATH: str = "cybermarket.db"

    # Каталог для хранения цифровых товаров (файлов)
    PRODUCTS_DIR: str = "products"

    # Ссылка на поддержку
    SUPPORT_URL: str = "https://t.me/support_username"

    # Настройки Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def admin_ids_list(self) -> list[int]:
        """Возвращает список ID администраторов."""
        return self.ADMIN_IDS

    @property
    def bot_token(self) -> str:
        """Возвращает токен бота как строку."""
        return self.BOT_TOKEN.get_secret_value()

    @property
    def yookassa_secret_key(self) -> str:
        """Возвращает секретный ключ YooKassa как строку."""
        return self.YOOKASSA_SECRET_KEY.get_secret_value()

    @property
    def telegram_payment_token(self) -> str:
        """Возвращает токен Telegram Payments как строку."""
        return self.TELEGRAM_PAYMENT_TOKEN.get_secret_value()


# Создаём глобальный экземпляр настроек
settings = Settings()

# Создаём директорию для товаров, если её нет
os.makedirs(settings.PRODUCTS_DIR, exist_ok=True)
