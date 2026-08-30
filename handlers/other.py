# handlers/other.py
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from contextlib import suppress
from database import Database
from keyboards import get_main_menu
from config import settings

router = Router()
db = Database()


@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: types.Message):
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    text = (
        "👥 Реферальная программа\n\n"
        "Приглашай друзей и получай бонусы!\n\n"
        f"Твоя реферальная ссылка:\n"
        f"https://t.me/{message.bot.username}?start=ref_{user_id}\n\n"
        "За каждого приглашенного друга ты получаешь 5% от его первой покупки!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: types.Message):
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    text = (
        "⭐ Отзывы наших клиентов\n\n"
        "🌟 «Лучший магазин цифровых товаров! Всё быстро и качественно» — Алексей\n\n"
        "🌟 «Отличный выбор и мгновенная доставка. Рекомендую!» — Мария\n\n"
        "🌟 «Удобный интерфейс, всё понятно. Буду заказывать ещё!» — Дмитрий\n\n"
        "Хочешь оставить свой отзыв? Напиши нам в поддержку!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: types.Message):
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    text = (
        "🆘 Служба поддержки\n\n"
        "Если у тебя возникли вопросы или проблемы, мы всегда готовы помочь!\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @cybermarket_support\n"
        "🕐 Время работы: 24/7\n\n"
        "Опиши свою проблему — и мы ответим в ближайшее время!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu_callback(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()
    
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    with suppress(Exception):
        await callback.message.edit_text(
            "Главное меню:",
            reply_markup=get_main_menu(is_admin=is_admin)
        )
