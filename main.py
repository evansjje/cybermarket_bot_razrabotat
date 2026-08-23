# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database import Database
from keyboards import get_main_menu
from handlers import catalog, payment, admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Создание экземпляра базы данных
db = Database()

# Регистрация роутеров
dp.include_router(catalog.router)
dp.include_router(payment.router)
dp.include_router(admin.router)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Регистрация пользователя в базе данных
    await db.connect()
    
    # Проверяем, существует ли пользователь
    cursor = await db.connection.execute(
        "SELECT id FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    user = await cursor.fetchone()
    
    if not user:
        # Генерируем реферальный код
        import random
        import string
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Проверяем, есть ли реферальный код в аргументах
        args = message.text.split()
        referred_by = None
        if len(args) > 1:
            ref_code = args[1]
            cursor = await db.connection.execute(
                "SELECT id FROM users WHERE referral_code = ?",
                (ref_code,)
            )
            referrer = await cursor.fetchone()
            if referrer:
                referred_by = referrer[0]
        
        # Создаем нового пользователя
        await db.connection.execute(
            """INSERT INTO users (telegram_id, username, first_name, last_name, referral_code, referred_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, username, first_name, last_name, referral_code, referred_by)
        )
        await db.connection.commit()
        
        # Если пользователь пришел по реферальной ссылке, начисляем бонус
        if referred_by:
            await db.connection.execute(
                "UPDATE users SET balance = balance + 50 WHERE id = ?",
                (referred_by,)
            )
            await db.connection.commit()
    
    await message.answer(
        f"👋 Добро пожаловать в <b>CyberMarket</b>!\n\n"
        f"Здесь вы можете приобрести цифровые товары: скрипты, софт, мануалы и многое другое.\n\n"
        f"Используйте кнопки ниже для навигации:",
        reply_markup=get_main_menu()
    )


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Обработчик команды /admin"""
    if settings.is_admin(message.from_user.id):
        await admin.show_admin_panel(message)
    else:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")


@dp.message(Command("cart"))
async def cmd_cart(message: Message):
    """Обработчик команды /cart"""
    await catalog.show_cart(message)


@dp.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Обработчик команды /catalog"""
    await catalog.show_catalog(message)


@dp.message(Command("referral"))
async def cmd_referral(message: Message):
    """Обработчик команды /referral"""
    await catalog.show_referral_program(message)


@dp.message(Command("support"))
async def cmd_support(message: Message):
    """Обработчик команды /support"""
    await message.answer(
        "📞 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, свяжитесь с нами:\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @cybermarket_support\n\n"
        "Мы отвечаем в течение 24 часов!"
    )


@dp.message(Command("reviews"))
async def cmd_reviews(message: Message):
    """Обработчик команды /reviews"""
    await message.answer(
        "⭐️ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Купил скрипт для автоматизации, всё работает идеально» — Иван\n\n"
        "🌟 «Быстрая доставка, качественный товар. Рекомендую!» — Мария\n\n"
        "🌟 «Лучший выбор цифровых товаров. Поддержка отвечает мгновенно» — Алексей\n\n"
        "Хотите оставить отзыв? Напишите нам в поддержку!"
    )


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Запуск бота...")
    
    # Подключение к базе данных
    await db.connect()
    logger.info("База данных подключена")
    
    # Проверка наличия товаров в базе
    cursor = await db.connection.execute("SELECT COUNT(*) FROM products")
    count = await cursor.fetchone()
    if count[0] == 0:
        logger.info("База данных пуста. Добавьте товары через админ-панель.")
    
    logger.info("Бот успешно запущен!")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Остановка бота...")
    await db.close()
    await bot.session.close()
    logger.info("Бот остановлен")


async def main():
    """Главная функция запуска"""
    # Регистрация обработчиков запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
