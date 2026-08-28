from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import main_menu_kb
from config import settings

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    
    # Регистрация пользователя в БД
    await db.db.execute(
        "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )
    await db.db.commit()
    
    # Проверка на админа
    is_admin = user_id in settings.ADMIN_IDS
    
    # Отправка приветствия и главного меню
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket!\n\n"
        f"🛍 Здесь вы можете приобрести цифровые товары.\n"
        f"Выберите действие в меню ниже:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
