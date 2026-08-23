import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Settings
from database import Database
from handlers import catalog, payment, admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = Settings()


async def on_startup(bot: Bot, db: Database) -> None:
    """Действия при запуске бота."""
    await db.connect()
    await db.create_default_categories()
    logger.info("Бот запущен и готов к работе")


async def on_shutdown(bot: Bot, db: Database) -> None:
    """Действия при остановке бота."""
    await db.close()
    logger.info("Бот остановлен")


async def main() -> None:
    """Главная функция запуска бота."""
    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Инициализация хранилища состояний
    storage = MemoryStorage()
    
    # Инициализация диспетчера
    dp = Dispatcher(storage=storage)
    
    # Создание экземпляра базы данных
    db = Database(settings.DB_PATH)
    
    # Регистрация роутеров
    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    
    # Регистрация хуков жизненного цикла
    dp.startup.register(lambda: on_startup(bot, db))
    dp.shutdown.register(lambda: on_shutdown(bot, db))
    
    # Запуск бота
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
