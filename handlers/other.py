from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import main_menu_kb
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral(message: Message, db: Database):
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    await message.answer(
        f"👥 Реферальная программа\n\n"
        f"Приглашайте друзей и получайте бонусы!\n\n"
        f"Ваша реферальная ссылка:\n"
        f"🔗 {referral_link}\n\n"
        f"Поделитесь этой ссылкой с друзьями, "
        f"и когда они перейдут по ней, вы получите вознаграждение.",
        reply_markup=main_menu_kb(is_admin=user_id in settings.ADMIN_IDS)
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message, db: Database):
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    await message.answer(
        "⭐ Отзывы наших клиентов:\n\n"
        "💬 «Отличный магазин! Всё работает быстро и качественно!» — Алексей\n"
        "💬 «Лучшие цены на цифровые товары. Рекомендую!» — Мария\n"
        "💬 «Быстрая доставка и отличная поддержка. Спасибо!» — Дмитрий\n\n"
        "Хотите оставить отзыв? Напишите нам в поддержку! 👇",
        reply_markup=main_menu_kb(is_admin=user_id in settings.ADMIN_IDS)
    )


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message, db: Database):
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    await message.answer(
        "🆘 Поддержка CyberMarket\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "напишите нам в чат поддержки:\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @CyberMarketSupport\n\n"
        "Мы отвечаем в течение 24 часов!",
        reply_markup=main_menu_kb(is_admin=user_id in settings.ADMIN_IDS)
    )
