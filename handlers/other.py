# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from contextlib import suppress

from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral(message: Message, db: Database):
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        "Поделитесь этой ссылкой с друзьями, "
        "и когда они перейдут по ней, вы получите вознаграждение."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    
    await message.answer(
        text,
        reply_markup=builder.as_markup()
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message, db: Database):
    """Обработчик кнопки Отзывы"""
    text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Всё работает быстро и качественно» — Алексей\n\n"
        "🌟 «Лучшие цены на рынке, рекомендую!» — Мария\n\n"
        "🌟 «Удобный интерфейс, быстрое получение товара» — Дмитрий\n\n"
        "Хотите оставить отзыв? Напишите нам в поддержку!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='🆘 Поддержка', callback_data='support'),
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')
    )
    
    await message.answer(
        text,
        reply_markup=builder.as_markup()
    )


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message, db: Database):
    """Обработчик кнопки Поддержка"""
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "напишите нам в чат поддержки:\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @cybermarket_support\n\n"
        "Мы отвечаем в течение 24 часов!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    
    await message.answer(
        text,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback, db: Database):
    """Возврат в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    with suppress(Exception):
        await callback.message.edit_text(
            "🏠 Главное меню\n\n"
            "Выберите раздел:",
            reply_markup=main_menu(is_admin=is_admin)
        )


@router.callback_query(F.data == 'support')
async def support_callback(callback, db: Database):
    """Обработка callback поддержки"""
    await callback.answer()
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "напишите нам в чат поддержки:\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @cybermarket_support\n\n"
        "Мы отвечаем в течение 24 часов!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    
    with suppress(Exception):
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
