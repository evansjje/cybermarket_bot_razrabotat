# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, Update
from database import Database
from keyboards import main_menu_kb

router = Router()
db = Database()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Регистрация пользователя в базе данных
    await db.add_user(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )

    # Отправка приветственного сообщения и главного меню
    await message.answer(
        f"👋 Добро пожаловать, {first_name}!\n\n"
        "🛍 Это магазин цифровых товаров.\n"
        "Здесь вы найдете скрипты, софт и мануалы.\n\n"
        "Выберите раздел в меню ниже:",
        reply_markup=main_menu_kb()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu для возврата в главное меню"""
    await message.answer(
        "📋 Главное меню:",
        reply_markup=main_menu_kb()
    )


@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message):
    """Возврат в главное меню по кнопке"""
    await message.answer(
        "📋 Главное меню:",
        reply_markup=main_menu_kb()
    )


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Возврат в главное меню по инлайн-кнопке"""
    await callback.message.answer(
        "📋 Главное меню:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()
