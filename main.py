# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from database import init_db
from handlers import start, catalog, cart, admin, other

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    await init_db()

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)
    dp.include_router(other.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
