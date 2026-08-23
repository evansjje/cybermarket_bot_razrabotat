import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import db
from handlers import catalog, payment, admin
from keyboards import get_main_menu

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Действия при запуске бота."""
    logger.info("🚀 Бот запускается...")
    
    # Подключаемся к базе данных
    await db.connect()
    logger.info("✅ База данных подключена")
    
    # Создаем директорию для товаров, если её нет
    os.makedirs(settings.PRODUCTS_DIR, exist_ok=True)
    
    # Устанавливаем команды бота
    await bot.set_my_commands([
        {"command": "start", "description": "🚀 Запустить бота"},
        {"command": "catalog", "description": "🛍️ Открыть каталог"},
        {"command": "cart", "description": "🛒 Открыть корзину"},
        {"command": "admin", "description": "⚙️ Админ-панель"},
        {"command": "help", "description": "❓ Помощь"}
    ])
    
    logger.info("✅ Команды установлены")
    logger.info("🎉 Бот готов к работе!")


async def on_shutdown(bot: Bot) -> None:
    """Действия при остановке бота."""
    logger.info("🛑 Бот останавливается...")
    await db.close()
    logger.info("✅ База данных закрыта")


async def main() -> None:
    """Точка входа в приложение."""
    
    # Проверяем наличие токена
    if settings.bot_token == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Не установлен BOT_TOKEN! Укажите токен в .env файле")
        return
    
    # Создаем экземпляр бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создаем диспетчер с хранилищем состояний
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем роутеры
    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    
    # Регистрируем обработчики запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запускаем бота
    logger.info("⚡ Запуск бота...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
