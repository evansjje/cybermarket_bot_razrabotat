# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral(message: Message):
    """Обработчик кнопки Рефералка."""
    user_id = message.from_user.id
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        "За каждого приглашённого друга вы получаете 5% от его первой покупки."
    )

    await message.answer(
        text,
        reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS),
        parse_mode='HTML'
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message):
    """Обработчик кнопки Отзывы."""
    user_id = message.from_user.id

    text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Всё пришло мгновенно, ключ активировался без проблем.» — Алексей\n\n"
        "🌟 «Пользуюсь сервисом уже полгода, ни разу не подвели. Рекомендую!» — Мария\n\n"
        "🌟 «Быстрая поддержка, качественные товары. 10/10!» — Дмитрий\n\n"
        "Хотите оставить отзыв? Напишите нам в поддержку!"
    )

    await message.answer(
        text,
        reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS),
        parse_mode='HTML'
    )


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message):
    """Обработчик кнопки Поддержка."""
    user_id = message.from_user.id

    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, наши операторы всегда готовы помочь!\n\n"
        "📧 Email: support@cybermarket.shop\n"
        "💬 Telegram: @CyberMarketSupport\n\n"
        "⏰ Время работы: 24/7"
    )

    await message.answer(
        text,
        reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню."""
    await callback.answer()

    try:
        user_id = callback.from_user.id
        await callback.message.edit_text(
            "🏠 Вы вернулись в главное меню.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🛍 Каталог', callback_data='back_to_categories')]
            ])
        )
    except Exception:
        pass
