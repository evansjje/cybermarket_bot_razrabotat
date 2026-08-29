from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from database import db
from keyboards import main_menu
from config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Регистрация пользователя в БД
    await db.db.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name)
    )
    await db.db.commit()

    # Проверка, является ли пользователь админом
    is_admin = user_id in settings.ADMIN_IDS

    # Отправка главного меню
    await message.answer(
        f"👋 Добро пожаловать, {first_name}!\n"
        "🛍 Выберите раздел меню:",
        reply_markup=main_menu(is_admin=is_admin)
    )
