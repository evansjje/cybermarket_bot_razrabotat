# main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import settings
from database import init_db
from handlers import start, catalog, cart, admin, other


async def main() -> None:
    """Точка входа в бота"""
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Инициализация базы данных
    await init_db()

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)
    dp.include_router(other.router)

    # Запуск поллинга
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
