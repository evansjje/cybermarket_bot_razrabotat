# handlers/start.py
from aiogram import Router, types
from aiogram.filters import CommandStart
from database import Database
from keyboards import get_main_menu
from config import settings

router = Router()
db = Database()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # Регистрация пользователя в БД (создание записи в cart, если нет)
    try:
        await db.init_db()
        # Проверяем, есть ли пользователь в корзине (как маркер регистрации)
        cart = await db.get_cart(user_id)
        if not cart:
            # Добавляем пустую запись для регистрации (или просто логируем)
            pass
    except Exception:
        pass

    # Проверяем, является ли пользователь админом
    is_admin = user_id in settings.ADMIN_IDS

    # Отправляем главное меню
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket, {message.from_user.first_name}!\n"
        f"🛍 Здесь ты можешь купить цифровые товары.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )
