# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database import Database
from handlers import catalog, payment, admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot) -> None:
    """Установка команд бота"""
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/catalog", description="Открыть каталог"),
        BotCommand(command="/cart", description="Открыть корзину"),
        BotCommand(command="/help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot, db: Database) -> None:
    """Действия при запуске бота"""
    logger.info("Бот запускается...")
    await db.init_db()
    await set_commands(bot)
    logger.info("База данных инициализирована")
    logger.info("Бот успешно запущен!")


async def on_shutdown(bot: Bot, db: Database) -> None:
    """Действия при остановке бота"""
    logger.info("Бот останавливается...")
    await bot.session.close()
    logger.info("Бот остановлен")


async def main() -> None:
    """Главная функция запуска бота"""
    # Проверка токена
    if settings.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Пожалуйста, установите BOT_TOKEN в .env файле!")
        return

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    db = Database()
    
    # Регистрация роутеров
    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    
    # Регистрация обработчиков запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск бота
    try:
        await dp.start_polling(bot, db=db)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
