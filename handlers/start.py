# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import Database
from keyboards import main_menu
from config import settings

router = Router()
db = Database()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    await db.connect()
    
    # Регистрация пользователя в БД
    await db.db.execute(
        'INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
        (user.id, user.username, user.first_name, user.last_name)
    )
    await db.commit()
    
    # Проверка на админа
    is_admin = user.id in settings.ADMIN_IDS
    
    await message.answer(
        f"👋 Добро пожаловать, {user.first_name or 'пользователь'}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары:\n"
        "🎮 Цифровые игры\n"
        "💎 Подписки\n"
        "🎁 Подарочные карты\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin)
    )
    
    await db.close()
