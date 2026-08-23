from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import add_user
from keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Регистрация пользователя в БД
    await add_user(user_id, username, first_name, last_name)

    # Отправка главного меню
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket!\n\n"
        f"Здесь вы можете приобрести цифровые товары: скрипты, курсы и софт.\n"
        f"Используйте кнопки ниже для навигации:",
        reply_markup=main_menu_keyboard(user_id)
    )
