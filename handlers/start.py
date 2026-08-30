# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from database import Database
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    # Регистрация пользователя в БД
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Проверяем, существует ли пользователь
    cursor = await db.db.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    existing_user = await cursor.fetchone()

    if not existing_user:
        await db.db.execute(
            'INSERT INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
            (user_id, username, first_name, last_name)
        )
        await db.db.commit()

    # Определяем, является ли пользователь админом
    is_admin = user_id in settings.ADMIN_IDS

    # Отправляем приветственное сообщение и главное меню
    await message.answer(
        f"👋 Добро пожаловать, {first_name or 'пользователь'}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите раздел в меню ниже:",
        reply_markup=main_menu(is_admin)
    )
