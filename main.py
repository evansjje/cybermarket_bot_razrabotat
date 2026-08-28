import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database import Database

# Импортируем роутеры
from handlers import start, catalog, cart, admin, other

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main() -> None:
    """Точка входа в приложение"""
    
    # Инициализация базы данных
    db = Database()
    await db.connect()
    logger.info("База данных подключена и готова к работе")
    
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
    
    # Передаем db в обработчики через middleware или через параметры
    # В aiogram 3 можно использовать dependency injection через параметры функций
    # Но для простоты будем передавать db через глобальную переменную или через middleware
    
    # Создаем middleware для передачи db в обработчики
    from aiogram import BaseMiddleware
    from aiogram.types import TelegramObject
    from typing import Callable, Dict, Any, Awaitable
    
    class DatabaseMiddleware(BaseMiddleware):
        async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
        ) -> Any:
            data['db'] = db
            return await handler(event, data)
    
    # Регистрируем middleware
    dp.update.middleware(DatabaseMiddleware())
    
    # Запуск бота
    try:
        logger.info("Бот запущен и готов к работе")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
        sys.exit(0)
