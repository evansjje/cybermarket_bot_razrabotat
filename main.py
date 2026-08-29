# main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import db
from handlers import start, catalog, cart, admin, other

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    """Точка входа в бота"""
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение к базе данных
    await db.connect()

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)
    dp.include_router(other.router)

    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        if db.db:
            await db.db.close()


if __name__ == '__main__':
    asyncio.run(main())
