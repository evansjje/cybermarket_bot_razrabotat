# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from database import Database
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    # Регистрация пользователя в БД
    await db.db.execute(
        """
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (user_id, username, first_name)
    )
    await db.db.commit()

    # Проверка на админа
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        f"👋 Добро пожаловать, {first_name}!\n\n"
        "🛍 Здесь ты можешь приобрести цифровые товары.\n"
        "Выбери раздел в меню ниже:",
        reply_markup=main_menu(is_admin=is_admin)
    )
