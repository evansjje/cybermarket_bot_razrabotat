from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_connection
from keyboards import get_main_menu

router = Router()


@router.message(F.text == "👥 Рефералка")
async def referral_info(message: Message) -> None:
    """Показать реферальную ссылку и баланс"""
    user_id = message.from_user.id
    bot_username = (await message.bot.me()).username
    
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT balance, referrer_id FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE referrer_id = ?",
            (user_id,)
        )
        referrals_count = (await cursor.fetchone())["cnt"]
    finally:
        await conn.close()

    if not user:
        await message.answer("❌ Пользователь не найден. Нажмите /start")
        return

    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{ref_link}</code>\n\n"
        f"💰 Ваш баланс: <b>{user['balance']}₽</b>\n"
        f"👤 Приглашено пользователей: <b>{referrals_count}</b>\n\n"
        f"Приглашайте друзей и получайте бонусы на баланс!"
    )
    
    await message.answer(text)


@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message) -> None:
    """Показать отзывы покупателей"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="leave_review")],
            [InlineKeyboardButton(text="📝 Все отзывы", callback_data="all_reviews")]
        ]
    )
    
    text = (
        "⭐ <b>Отзывы наших покупателей</b>\n\n"
        "🟢 <b>Алексей:</b> \"Отличный магазин! Всё пришло мгновенно, "
        "скрипты работают идеально. Рекомендую!\"\n\n"
        "🟢 <b>Мария:</b> \"Купила курс по Python, всё чётко и понятно. "
        "Поддержка отвечает быстро. 10/10!\"\n\n"
        "🟢 <b>Дмитрий:</b> \"Пользуюсь софтом уже месяц, всё стабильно. "
        "Цены адекватные, товары качественные.\"\n\n"
        "🟢 <b>Елена:</b> \"Заказывала скрипт для автоматизации, "
        "всё работает как заявлено. Спасибо!\"\n\n"
        "⬇️ Хотите поделиться своим мнением? Жмите кнопку ниже!"
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "leave_review")
async def leave_review(callback: CallbackQuery) -> None:
    """Оставить отзыв"""
    await callback.message.edit_text(
        "📝 <b>Оставить отзыв</b>\n\n"
        "Напишите ваш отзыв в чат, и он будет опубликован после модерации.\n\n"
        "Формат: <code>Ваш отзыв</code>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data == "all_reviews")
async def all_reviews(callback: CallbackQuery) -> None:
    """Показать все отзывы"""
    text = (
        "📚 <b>Все отзывы</b>\n\n"
        "⭐ <b>Алексей:</b> \"Отличный магазин! Всё пришло мгновенно, "
        "скрипты работают идеально. Рекомендую!\"\n\n"
        "⭐ <b>Мария:</b> \"Купила курс по Python, всё чётко и понятно. "
        "Поддержка отвечает быстро. 10/10!\"\n\n"
        "⭐ <b>Дмитрий:</b> \"Пользуюсь софтом уже месяц, всё стабильно. "
        "Цены адекватные, товары качественные.\"\n\n"
        "⭐ <b>Елена:</b> \"Заказывала скрипт для автоматизации, "
        "всё работает как заявлено. Спасибо!\"\n\n"
        "⭐ <b>Игорь:</b> \"Быстрая доставка, качественный товар. "
        "Обязательно вернусь ещё!\"\n\n"
        "⭐ <b>Ольга:</b> \"Лучший магазин цифровых товаров! "
        "Всё честно и без обмана.\""
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_reviews")
async def back_to_reviews(callback: CallbackQuery) -> None:
    """Вернуться к отзывам"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="leave_review")],
            [InlineKeyboardButton(text="📝 Все отзывы", callback_data="all_reviews")]
        ]
    )
    
    text = (
        "⭐ <b>Отзывы наших покупателей</b>\n\n"
        "🟢 <b>Алексей:</b> \"Отличный магазин! Всё пришло мгновенно, "
        "скрипты работают идеально. Рекомендую!\"\n\n"
        "🟢 <b>Мария:</b> \"Купила курс по Python, всё чётко и понятно. "
        "Поддержка отвечает быстро. 10/10!\"\n\n"
        "🟢 <b>Дмитрий:</b> \"Пользуюсь софтом уже месяц, всё стабильно. "
        "Цены адекватные, товары качественные.\"\n\n"
        "🟢 <b>Елена:</b> \"Заказывала скрипт для автоматизации, "
        "всё работает как заявлено. Спасибо!\"\n\n"
        "⬇️ Хотите поделиться своим мнением? Жмите кнопку ниже!"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(F.text == "🆘 Поддержка")
async def support_info(message: Message) -> None:
    """Показать контакты поддержки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Написать в поддержку", url="https://t.me/support")],
            [InlineKeyboardButton(text="📖 FAQ", callback_data="faq")]
        ]
    )
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, мы всегда готовы помочь!\n\n"
        "📨 <b>Способы связи:</b>\n"
        "• Telegram: @support\n"
        "• Email: support@cybermarket.ru\n"
        "• Время работы: 24/7\n\n"
        "⏱ Среднее время ответа: до 15 минут\n\n"
        "📖 Также вы можете ознакомиться с частыми вопросами в разделе FAQ."
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery) -> None:
    """Показать FAQ"""
    text = (
        "📖 <b>Часто задаваемые вопросы</b>\n\n"
        "❓ <b>Как получить товар после оплаты?</b>\n"
        "После оплаты товар автоматически отправляется вам в чат.\n\n"
        "❓ <b>Как долго обрабатывается заказ?</b>\n"
        "Все заказы обрабатываются мгновенно в автоматическом режиме.\n\n"
        "❓ <b>Есть ли гарантия на товары?</b>\n"
        "Да, на все товары предоставляется гарантия 30 дней.\n\n"
        "❓ <b>Как вернуть деньги?</b>\n"
        "Если товар не работает, напишите в поддержку в течение 24 часов.\n\n"
        "❓ <b>Как работает реферальная программа?</b>\n"
        "Приглашайте друзей по своей ссылке и получайте бонусы на баланс."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_support")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_support")
async def back_to_support(callback: CallbackQuery) -> None:
    """Вернуться к поддержке"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Написать в поддержку", url="https://t.me/support")],
            [InlineKeyboardButton(text="📖 FAQ", callback_data="faq")]
        ]
    )
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, мы всегда готовы помочь!\n\n"
        "📨 <b>Способы связи:</b>\n"
        "• Telegram: @support\n"
        "• Email: support@cybermarket.ru\n"
        "• Время работы: 24/7\n\n"
        "⏱ Среднее время ответа: до 15 минут\n\n"
        "📖 Также вы можете ознакомиться с частыми вопросами в разделе FAQ."
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
