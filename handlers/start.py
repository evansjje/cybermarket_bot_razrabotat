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
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    await add_user(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )

    await message.answer(
        f"👋 Добро пожаловать в CyberMarket_Bot!\n\n"
        f"🛍 Здесь ты можешь приобрести цифровые товары: скрипты, курсы и софт.\n\n"
        f"Выбери раздел в меню ниже:",
        reply_markup=main_menu_kb(user_id)
    )
