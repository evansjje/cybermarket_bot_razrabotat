from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import Database
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database) -> None:
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Проверяем, есть ли пользователь в БД
    existing_user = await db.get_user(user_id)
    if not existing_user:
        # Создаем нового пользователя
        await db.add_user(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

    # Отправляем приветственное сообщение и главное меню
    await message.answer(
        f"👋 Добро пожаловать, {first_name or 'пользователь'}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите раздел в меню ниже:",
        reply_markup=main_menu()
    )
