# handlers/start.py
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import Database
from keyboards import main_menu_kb

router = Router()
db = Database()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Регистрация пользователя
    await db.add_user(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )

    # Проверка на админа
    is_admin = user_id == settings.ADMIN_ID

    # Приветственное сообщение
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket, {first_name}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары:\n"
        "• Программы и скрипты\n"
        "• Аккаунты и ключи\n"
        "• Курсы и материалы\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


# Импортируем settings для проверки админа
from config import settings
