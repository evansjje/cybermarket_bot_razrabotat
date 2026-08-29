import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import settings
from database import Database
from handlers import start, catalog, cart, admin, other

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    # Инициализация базы данных
    db = Database()
    await db.connect()
    
    # Передаем db в роутеры
    start.db = db
    catalog.db = db
    cart.db = db
    admin.db = db
    other.db = db
    
    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)
    dp.include_router(other.router)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
