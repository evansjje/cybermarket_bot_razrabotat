# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message
from keyboards import main_menu_kb

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: Message) -> None:
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашай друзей и получай бонусы!\n\n"
        f"🔗 Твоя реферальная ссылка:\n"
        f"<code>https://t.me/{(await message.bot.me()).username}?start=ref_{user_id}</code>\n\n"
        "За каждого приглашенного друга ты получаешь бонус на счет.",
        reply_markup=main_menu_kb(user_id)
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message) -> None:
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    await message.answer(
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Всё работает быстро и качественно» — Алексей\n"
        "🌟 «Лучшие цены и мгновенная доставка товара» — Мария\n"
        "🌟 «Рекомендую! Уже не первый раз покупаю здесь» — Дмитрий\n\n"
        "Хочешь оставить свой отзыв? Напиши нам в поддержку!",
        reply_markup=main_menu_kb(user_id)
    )


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message) -> None:
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    await message.answer(
        "🆘 <b>Поддержка</b>\n\n"
        "Если у тебя возникли вопросы или проблемы, напиши нам:\n\n"
        "📧 Email: support@cybermarket.shop\n"
        "💬 Telegram: @CyberMarketSupport\n\n"
        "Мы отвечаем в течение 24 часов!",
        reply_markup=main_menu_kb(user_id)
    )
