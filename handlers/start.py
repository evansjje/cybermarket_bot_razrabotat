# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database) -> None:
    """Обработчик команды /start - регистрация пользователя и показ главного меню."""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    # Регистрация пользователя в БД
    await db.db.execute(
        """
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (user_id, username, first_name)
    )
    await db.db.commit()

    # Проверка, является ли пользователь админом
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        f"👋 Добро пожаловать, {first_name}!\n"
        "🛍 Здесь ты можешь приобрести цифровые товары.\n"
        "Выбери действие в меню ниже:",
        reply_markup=main_menu(is_admin=is_admin)
    )
