# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import main_menu_kb
from config import settings

router = Router()
db = Database()


class Registration(StatesGroup):
    waiting_for_referral = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start - регистрация пользователя и показ главного меню."""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    
    # Проверяем реферальный код из аргументов команды
    referral_code = None
    args = message.text.split()
    if len(args) > 1:
        referral_code = args[1]
    
    # Регистрируем пользователя
    await db.add_user(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        referral_code=referral_code
    )
    
    # Проверяем, является ли пользователь админом
    is_admin = (user_id == settings.ADMIN_ID)
    
    # Показываем главное меню
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket, {first_name}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары:\n"
        "• Программы и скрипты\n"
        "• Курсы и обучение\n"
        "• Аккаунты и подписки\n\n"
        "Выберите раздел в меню ниже:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    
    await state.clear()


@router.message(F.text == "🛍 Каталог")
async def catalog_handler(message: Message):
    """Обработка кнопки Каталог."""
    from handlers.catalog import show_categories
    await show_categories(message)


@router.message(F.text == "🛒 Корзина")
async def cart_handler(message: Message):
    """Обработка кнопки Корзина."""
    from handlers.cart import show_cart
    await show_cart(message)


@router.message(F.text == "👥 Рефералка")
async def referral_handler(message: Message):
    """Обработка кнопки Рефералка."""
    from handlers.other import referral_program
    await referral_program(message)


@router.message(F.text == "⭐ Отзывы")
async def reviews_handler(message: Message):
    """Обработка кнопки Отзывы."""
    from handlers.other import show_reviews
    await show_reviews(message)


@router.message(F.text == "🆘 Поддержка")
async def support_handler(message: Message):
    """Обработка кнопки Поддержка."""
    from handlers.other import show_support
    await show_support(message)


@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel_handler(message: Message):
    """Обработка кнопки Админ-панель."""
    if message.from_user.id == settings.ADMIN_ID:
        from handlers.admin import show_admin_panel
        await show_admin_panel(message)
    else:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню."""
    user_id = callback.from_user.id
    is_admin = (user_id == settings.ADMIN_ID)
    await callback.message.answer(
        "Вы вернулись в главное меню:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    await callback.answer()
