# main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import Database

# Импортируем все роутеры
from handlers import start, catalog, cart, admin, other

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def main():
    """Точка входа в бота."""
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализация базы данных
    db = Database()
    await db.connect()

    # Регистрация всех роутеров
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)
    dp.include_router(other.router)

    # Передаем db в контекст бота
    dp.workflow_data['db'] = db

    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())
