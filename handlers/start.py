from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import settings
from database import Database
from keyboards import main_menu

router = Router()
db = Database()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Проверяем, есть ли реферер в deep link
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
        except ValueError:
            pass
    
    # Сохраняем пользователя в БД
    await db.db.execute(
        "INSERT OR IGNORE INTO users (id, username, first_name, last_name, referrer_id) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, first_name, last_name, referrer_id)
    )
    await db.db.commit()
    
    # Проверяем, является ли пользователь админом
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket, {first_name or 'пользователь'}!\n\n"
        "🛍 Здесь ты можешь приобрести цифровые товары.\n"
        "Выбери нужный раздел в меню ниже:",
        reply_markup=main_menu(is_admin)
    )
