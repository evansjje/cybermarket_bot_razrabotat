# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from database import db
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Регистрация пользователя в БД
    await db.db.execute(
        """
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, username, first_name, last_name)
    )
    await db.db.commit()

    # Проверка, является ли пользователь админом
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        f"👋 Добро пожаловать в CyberMarket!\n\n"
        f"🛍 Здесь вы можете приобрести цифровые товары.\n"
        f"Выберите раздел в меню ниже:",
        reply_markup=main_menu(is_admin=is_admin)
    )
