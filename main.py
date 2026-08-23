import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database import Database
from handlers import catalog, payment, admin
from keyboards import main_menu_kb

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot, db: Database):
    await db.connect()
    await bot.set_my_commands([
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/catalog", description="Открыть каталог"),
        BotCommand(command="/cart", description="Открыть корзину"),
        BotCommand(command="/help", description="Помощь"),
    ])


async def on_shutdown(bot: Bot, db: Database):
    await db.close()


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    db = Database()
    dp["db"] = db

    # Initialize db in handlers
    catalog.db = db
    payment.db = db
    admin.db = db

    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    @dp.message(commands=["start"])
    async def cmd_start(message):
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""

        # Register user if not exists
        user = await db.get_user(user_id)
        if not user:
            await db.add_user(user_id, username, first_name, last_name)

        await message.answer(
            f"👋 Добро пожаловать, {first_name}!\n"
            "🛍 Здесь вы можете приобрести цифровые товары: скрипты, софт и мануалы.\n"
            "Выберите раздел в меню ниже:",
            reply_markup=main_menu_kb()
        )

    @dp.message(commands=["catalog"])
    async def cmd_catalog(message):
        await catalog.show_catalog(message)

    @dp.message(commands=["cart"])
    async def cmd_cart(message):
        user_id = message.from_user.id
        cart_items = await db.get_cart(user_id)
        if not cart_items:
            await message.answer("🛒 Ваша корзина пуста")
            return

        text = "🛒 Ваша корзина:\n\n"
        total = 0
        for item in cart_items:
            product = await db.get_product(item[1])
            if product:
                text += f"📦 {product[1]} — {product[3]} руб. x {item[2]}\n"
                total += product[3] * item[2]

        text += f"\n💰 Итого: {total} руб."
        await message.answer(text)

    @dp.message(commands=["help"])
    async def cmd_help(message):
        await message.answer(
            "📚 Помощь:\n"
            "🛍 Каталог — просмотр товаров\n"
            "🛒 Корзина — ваши покупки\n"
            "👥 Реферальная программа — приглашайте друзей и получайте бонусы\n"
            "⭐️ Отзывы — отзывы покупателей\n"
            "📞 Поддержка — связь с администрацией"
        )

    await on_startup(bot, db)
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot, db)


if __name__ == "__main__":
    asyncio.run(main())
