import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from database import Database

# Импортируем роутеры
from handlers import start, catalog, cart, admin, other

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Создаем экземпляр базы данных
db = Database()

async def main():
    """Главная функция запуска бота"""
    # Подключаемся к базе данных
    await db.connect()
    
    # Передаем экземпляр БД во все роутеры
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
    
    # Запускаем polling
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()

if __name__ == '__main__':
    asyncio.run(main())
