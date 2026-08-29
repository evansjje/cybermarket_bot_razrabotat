from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database):
    """Обработчик команды /start"""
    await state.clear()
    
    # Регистрация пользователя в БД
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    try:
        await db.db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.db.commit()
    except Exception:
        pass
    
    # Проверка на админа
    is_admin = user_id in settings.ADMIN_IDS
    
    # Отправка приветствия и главного меню
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket!\n\n"
        f"🛍 Здесь вы можете приобрести цифровые товары.\n"
        f"💰 Оплата производится через криптовалюту или банковские карты.\n\n"
        f"Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin)
    )
