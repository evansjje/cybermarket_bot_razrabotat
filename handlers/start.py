# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database import Database
from keyboards import get_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    # Регистрация пользователя в БД
    await db.db.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name)
    )
    await db.db.commit()
    
    await message.answer(
        f"👋 Добро пожаловать, {first_name}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_menu(user_id)
    )
