from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Регистрация пользователя в БД
    await db.db.execute(
        "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )
    await db.db.commit()

    # Проверка, является ли пользователь администратором
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        f"👋 Добро пожаловать, {first_name or 'пользователь'}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin=is_admin)
    )
