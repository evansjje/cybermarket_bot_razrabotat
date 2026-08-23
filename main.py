# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import Database
from handlers import catalog, payment, admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, db: Database) -> None:
    """Действия при запуске бота"""
    await db.connect()
    logger.info("Database connected successfully")
    
    # Уведомление администраторов о запуске
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🚀 Бот CyberMarket запущен и готов к работе!"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")


async def on_shutdown(bot: Bot, db: Database) -> None:
    """Действия при остановке бота"""
    await db.close()
    logger.info("Database connection closed")


async def main() -> None:
    """Точка входа в приложение"""
    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Создание экземпляра базы данных
    db = Database()
    
    # Регистрация роутеров
    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    
    # Регистрация функций запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Передача зависимостей в роутеры
    dp.workflow_data.update({
        'db': db,
        'bot': bot
    })
    
    logger.info("Starting CyberMarket Bot...")
    
    try:
        # Запуск бота
        await dp.start_polling(bot, db=db)
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
