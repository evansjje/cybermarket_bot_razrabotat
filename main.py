# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from database import Database
from handlers import start, catalog, cart, admin, other

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Точка входа в приложение."""
    # Инициализация базы данных
    db = Database()
    await db.connect()
    logger.info("База данных подключена и инициализирована")

    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)
    dp.include_router(other.router)

    # Передача db в контекст для всех хэндлеров
    dp["db"] = db

    logger.info("Бот запущен и готов к работе")
    
    # Запуск поллинга
    try:
        await dp.start_polling(bot)
    finally:
        await db.db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
