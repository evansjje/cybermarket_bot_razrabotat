from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards import main_menu

router = Router()
db = Database()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Extract referral from start payload
    referral_id = None
    if message.text and len(message.text.split()) > 1:
        try:
            referral_id = int(message.text.split()[1])
        except ValueError:
            referral_id = None
    
    # Save user to database
    await db.db.execute(
        """INSERT OR IGNORE INTO users (id, username, first_name, last_name, referral_id) 
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, username, first_name, last_name, referral_id)
    )
    await db.db.commit()
    
    # Check if user is admin
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket, {first_name or 'пользователь'}!\n"
        f"🛍 Здесь вы можете приобрести цифровые товары.\n"
        f"Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin)
    )

@router.message(F.text == '🛍 Каталог')
async def catalog_handler(message: Message):
    from handlers.catalog import show_categories
    await show_categories(message)

@router.message(F.text == '🛒 Корзина')
async def cart_handler(message: Message):
    from handlers.cart import show_cart
    await show_cart(message)

@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: Message):
    from handlers.other import referral_system
    await referral_system(message)

@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message):
    from handlers.other import reviews
    await reviews(message)

@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message):
    from handlers.other import support
    await support(message)

@router.message(F.text == '⚡ Админ-панель')
async def admin_panel_handler(message: Message):
    if message.from_user.id in settings.ADMIN_IDS:
        from handlers.admin import admin_panel
        await admin_panel(message)
    else:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")

@router.callback_query()
async def handle_callback(callback: CallbackQuery):
    await callback.answer()
