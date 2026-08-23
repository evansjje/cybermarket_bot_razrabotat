from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import List, Optional


class Settings(BaseSettings):
    """Настройки бота через переменные окружения или .env файл."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Токен бота (обязательный)
    BOT_TOKEN: SecretStr = SecretStr("YOUR_BOT_TOKEN_HERE")
    
    # ID администратора (можно несколько через запятую)
    ADMIN_IDS: List[int] = [123456789]  # Замените на реальный ID
    
    # YooKassa (для платежей)
    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[SecretStr] = None
    
    # Telegram Payments (альтернатива YooKassa)
    TELEGRAM_PAYMENT_TOKEN: Optional[str] = None
    
    # Настройки базы данных
    DB_PATH: str = "cybermarket.db"
    
    # Настройки реферальной системы
    REFERRAL_BONUS_PERCENT: float = 10.0  # Процент от покупки рефералу
    REFERRAL_BONUS_FOR_REFERRER: float = 5.0  # Процент от покупки пригласившему
    
    # Валюта
    CURRENCY: str = "RUB"
    
    # Поддержка
    SUPPORT_USERNAME: str = "support_username"  # Username поддержки без @
    
    # Категории товаров по умолчанию
    DEFAULT_CATEGORIES: List[str] = ["Скрипты", "Софт", "Мануалы"]
    
    # Пути к файлам
    MEDIA_DIR: str = "media"
    
    @property
    def bot_token(self) -> str:
        """Возвращает токен бота как строку."""
        return self.BOT_TOKEN.get_secret_value()
    
    @property
    def yookassa_secret(self) -> Optional[str]:
        """Возвращает секретный ключ YooKassa как строку или None."""
        if self.YOOKASSA_SECRET_KEY:
            return self.YOOKASSA_SECRET_KEY.get_secret_value()
        return None
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Возвращает список ID администраторов."""
        return self.ADMIN_IDS
    
    @property
    def is_payment_configured(self) -> bool:
        """Проверяет, настроена ли хотя бы одна платежная система."""
        return bool(self.YOOKASSA_SHOP_ID and self.yookassa_secret) or bool(self.TELEGRAM_PAYMENT_TOKEN)


# Создаем глобальный экземпляр настроек
settings = Settings()
