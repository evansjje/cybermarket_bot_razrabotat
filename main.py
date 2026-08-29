import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import Database

# Импортируем роутеры
from handlers import start, catalog, cart, admin, other

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main() -> None:
    """Точка входа в приложение"""
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

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

    # Передаем db в хендлеры через middleware или через параметры
    # В aiogram 3 можно использовать dependency injection через middleware
    # Но проще передавать db через параметры в хендлерах, используя middleware

    # Создаем middleware для передачи db
    from aiogram import BaseMiddleware
    from aiogram.types import TelegramObject
    from typing import Callable, Dict, Any, Awaitable

    class DbMiddleware(BaseMiddleware):
        async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
        ) -> Any:
            data['db'] = db
            return await handler(event, data)

    # Применяем middleware ко всем роутерам
    for router in [start.router, catalog.router, cart.router, admin.router, other.router]:
        router.message.middleware(DbMiddleware())
        router.callback_query.middleware(DbMiddleware())

    # Запуск бота
    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
