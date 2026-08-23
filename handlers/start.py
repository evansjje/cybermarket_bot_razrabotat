from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import settings
from database import get_connection, init_db
from keyboards import get_main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Регистрация пользователя в БД
    conn = await get_connection()
    try:
        await conn.execute(
            """INSERT OR IGNORE INTO users (id, username, first_name, last_name)
               VALUES (?, ?, ?, ?)""",
            (user_id, username, first_name, last_name)
        )
        await conn.commit()
    finally:
        await conn.close()

    # Отправка главного меню
    keyboard = await get_main_menu(user_id)
    await message.answer(
        f"👋 Добро пожаловать, {first_name}!\n\n"
        "🛍 Это магазин цифровых товаров. Выберите раздел в меню ниже:",
        reply_markup=keyboard
    )
