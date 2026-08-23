import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если он есть)
load_dotenv()


class BotConfig(BaseModel):
    """Конфигурация бота"""
    token: str = Field(
        default=os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE"),
        description="Токен Telegram-бота"
    )
    admin_ids: list[int] = Field(
        default=[int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip()],
        description="Список ID администраторов"
    )


class PaymentConfig(BaseModel):
    """Конфигурация платежей"""
    yookassa_shop_id: str = Field(
        default=os.getenv("YOOKASSA_SHOP_ID", "YOUR_SHOP_ID"),
        description="ID магазина YooKassa"
    )
    yookassa_secret_key: str = Field(
        default=os.getenv("YOOKASSA_SECRET_KEY", "YOUR_SECRET_KEY"),
        description="Секретный ключ YooKassa"
    )
    telegram_payments_token: str = Field(
        default=os.getenv("TELEGRAM_PAYMENTS_TOKEN", "YOUR_TELEGRAM_PAYMENTS_TOKEN"),
        description="Токен Telegram Payments (для Stars)"
    )
    payment_provider: str = Field(
        default=os.getenv("PAYMENT_PROVIDER", "yookassa"),
        description="Платёжный провайдер: yookassa или telegram"
    )


class DatabaseConfig(BaseModel):
    """Конфигурация базы данных"""
    path: str = Field(
        default=os.getenv("DATABASE_PATH", "cybermarket.db"),
        description="Путь к файлу базы данных SQLite"
    )


class Settings(BaseSettings):
    """Основные настройки приложения"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    bot: BotConfig = BotConfig()
    payment: PaymentConfig = PaymentConfig()
    database: DatabaseConfig = DatabaseConfig()

    # Дополнительные настройки
    referral_bonus_percent: float = Field(
        default=float(os.getenv("REFERRAL_BONUS_PERCENT", "10")),
        description="Процент бонуса за реферальную программу"
    )
    referral_min_withdrawal: float = Field(
        default=float(os.getenv("REFERRAL_MIN_WITHDRAWAL", "100")),
        description="Минимальная сумма для вывода реферальных бонусов"
    )
    support_username: str = Field(
        default=os.getenv("SUPPORT_USERNAME", "support"),
        description="Username службы поддержки (без @)"
    )
    support_link: str = Field(
        default=os.getenv("SUPPORT_LINK", "https://t.me/support"),
        description="Ссылка на службу поддержки"
    )
    reviews_channel: str = Field(
        default=os.getenv("REVIEWS_CHANNEL", "https://t.me/reviews"),
        description="Ссылка на канал с отзывами"
    )

    @property
    def is_payment_configured(self) -> bool:
        """Проверка, настроены ли платежи"""
        if self.payment.payment_provider == "yookassa":
            return (
                self.payment.yookassa_shop_id != "YOUR_SHOP_ID"
                and self.payment.yookassa_secret_key != "YOUR_SECRET_KEY"
            )
        else:
            return self.payment.telegram_payments_token != "YOUR_TELEGRAM_PAYMENTS_TOKEN"

    @property
    def is_bot_configured(self) -> bool:
        """Проверка, настроен ли бот"""
        return self.bot.token != "YOUR_BOT_TOKEN_HERE"


# Создаём глобальный экземпляр настроек
settings = Settings()

# Экспортируем для удобства использования
bot_config = settings.bot
payment_config = settings.payment
database_config = settings.database
