from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from database import Database
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Проверяем, есть ли пользователь в БД
    user = await db.get_user(user_id)
    if not user:
        # Сохраняем нового пользователя
        await db.add_user(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

    # Проверяем, является ли пользователь админом
    from config import settings
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        f"👋 Добро пожаловать в CyberMarket!\n\n"
        f"🛍 Здесь вы можете приобрести цифровые товары.\n"
        f"Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin)
    )
