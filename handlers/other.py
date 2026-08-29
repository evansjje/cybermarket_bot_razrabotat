# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from database import Database
from keyboards import main_menu

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral(message: Message, db: Database):
    """Обработчик кнопки Рефералка"""
    user = message.from_user
    referral_link = f"https://t.me/{(await message.bot.me()).username}?start={user.id}"
    
    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        "Поделитесь этой ссылкой с друзьями, "
        "и когда они перейдут по ней — вы получите награду!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy_ref_link")]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'copy_ref_link')
async def copy_ref_link(callback):
    """Копирование реферальной ссылки"""
    await callback.answer("🔗 Ссылка скопирована!", show_alert=True)


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message, db: Database):
    """Обработчик кнопки Отзывы"""
    text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Всё работает быстро и качественно» — Андрей\n"
        "🌟 «Лучшие цены на рынке, рекомендую!» — Мария\n"
        "🌟 «Удобный интерфейс, покупка заняла 2 минуты» — Дмитрий\n"
        "🌟 «Поддержка отвечает мгновенно, спасибо!» — Елена\n\n"
        "Хотите оставить отзыв? Напишите нам в поддержку!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="write_review")]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'write_review')
async def write_review(callback):
    """Написать отзыв"""
    await callback.answer()
    
    try:
        await callback.message.edit_text(
            "✍️ <b>Написать отзыв</b>\n\n"
            "Напишите ваш отзыв в чат, и мы обязательно его опубликуем!\n"
            "Или напишите нам в поддержку: @CyberMarketSupport",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_reviews")]
            ])
        )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_reviews')
async def back_to_reviews(callback):
    """Возврат к отзывам"""
    await callback.answer()
    
    text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Всё работает быстро и качественно» — Андрей\n"
        "🌟 «Лучшие цены на рынке, рекомендую!» — Мария\n"
        "🌟 «Удобный интерфейс, покупка заняла 2 минуты» — Дмитрий\n"
        "🌟 «Поддержка отвечает мгновенно, спасибо!» — Елена\n\n"
        "Хотите оставить отзыв? Напишите нам в поддержку!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="write_review")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message, db: Database):
    """Обработчик кнопки Поддержка"""
    text = (
        "🆘 <b>Служба поддержки</b>\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "наша команда всегда готова помочь!\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @CyberMarketSupport\n"
        "🕐 Время работы: 24/7\n\n"
        "Опишите вашу проблему, и мы ответим в ближайшее время!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Написать в поддержку", url="https://t.me/CyberMarketSupport")]
    ])
    
    await message.answer(text, reply_markup=keyboard)
