# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards import main_menu
from config import settings

router = Router()
db = Database()


@router.message(F.text == '👥 Рефералка')
async def referral(message: Message):
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>https://t.me/{(await message.bot.me()).username}?start=ref_{user_id}</code>\n\n"
        "За каждого приглашённого друга вы получаете <b>5%</b> от его первой покупки.\n"
        "Бонусы начисляются автоматически после первой покупки друга.",
        reply_markup=main_menu(is_admin)
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message):
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Всё быстро и качественно» — Алексей\n"
        "🌟 «Лучшие цены на подписки, рекомендую!» — Мария\n"
        "🌟 «Покупка заняла 2 минуты, всё чётко» — Дмитрий\n"
        "🌟 «Удобный бот, всё на своих местах» — Елена\n\n"
        "Хотите оставить отзыв? Напишите нам в поддержку! 👇",
        reply_markup=main_menu(is_admin)
    )


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message):
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, мы всегда готовы помочь!\n\n"
        "📧 Email: support@cybermarket.ru\n"
        "💬 Telegram: @cybermarket_support\n"
        "🕐 Время работы: 24/7\n\n"
        "Опишите вашу проблему — мы ответим в ближайшее время!",
        reply_markup=main_menu(is_admin)
    )
