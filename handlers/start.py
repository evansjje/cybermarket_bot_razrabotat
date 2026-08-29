# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import settings
from database import Database
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    user = message.from_user
    await db.conn.execute(
        """
        INSERT OR IGNORE INTO users (id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        """,
        (user.id, user.username, user.first_name, user.last_name)
    )
    await db.conn.commit()

    is_admin = user.id in settings.ADMIN_IDS
    await message.answer(
        f"👋 Добро пожаловать, {user.first_name}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin)
    )
