from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import Database
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database) -> None:
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Проверяем, есть ли пользователь в базе данных
    async with db.db.execute(
        "SELECT id FROM users WHERE id = ?", (user_id,)
    ) as cursor:
        existing_user = await cursor.fetchone()

    if not existing_user:
        # Сохраняем нового пользователя
        await db.db.execute(
            """
            INSERT INTO users (id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, first_name, last_name),
        )
        await db.db.commit()

    # Проверяем, является ли пользователь админом
    from config import settings
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        f"👋 Добро пожаловать, {first_name or 'пользователь'}!\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin=is_admin),
    )
