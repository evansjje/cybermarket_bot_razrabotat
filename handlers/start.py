# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import add_user
from keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start"""
    user = message.from_user
    await add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    await message.answer(
        f"👋 Добро пожаловать, {user.first_name or 'пользователь'}!\n\n"
        "🛍 Здесь ты можешь приобрести цифровые товары.\n"
        "Выбери раздел в меню ниже:",
        reply_markup=main_menu_kb(user.id)
    )
