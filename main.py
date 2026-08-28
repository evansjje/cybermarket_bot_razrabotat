# main.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database import Database

# Импортируем роутеры
from handlers import start, catalog, cart, admin, other

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    """Установка команд бота"""
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/admin", description="Админ-панель"),
    ]
    await bot.set_my_commands(commands)


async def main():
    """Точка входа в приложение"""
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Инициализация базы данных
    db = Database()
    await db.connect()
    logger.info("База данных подключена")

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)
    dp.include_router(other.router)

    # Установка команд бота
    await set_commands(bot)

    # Запуск бота
    logger.info("Бот запущен и готов к работе")
    try:
        await dp.start_polling(bot, db=db)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
