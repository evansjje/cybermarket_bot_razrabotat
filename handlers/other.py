# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral(message: Message, db: Database) -> None:
    """Обработчик кнопки '👥 Рефералка'."""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    # Формируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    # Получаем количество приглашенных пользователей
    invited_count = 0
    try:
        async with db.db.execute(
            "SELECT COUNT(*) as count FROM users WHERE referred_by = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                invited_count = row['count'] if isinstance(row, dict) else row[0]
    except Exception:
        pass
    
    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено друзей: <b>{invited_count}</b>\n\n"
        f"💰 За каждого приглашенного друга вы получаете бонусы!\n"
        f"Поделитесь ссылкой с друзьями и получайте вознаграждения."
    )
    
    # Кнопка для возврата в меню
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    
    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message, db: Database) -> None:
    """Обработчик кнопки '⭐ Отзывы'."""
    text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 <b>Иван</b>: «Отличный магазин! Всё пришло мгновенно, товар качественный. Рекомендую!»\n\n"
        "🌟 <b>Мария</b>: «Быстрая доставка, удобная оплата. Уже не первый раз покупаю здесь!»\n\n"
        "🌟 <b>Алексей</b>: «Лучший бот для покупки цифровых товаров. Всё чётко и без проблем!»\n\n"
        "🌟 <b>Дмитрий</b>: «Понравился сервис, всё работает отлично. Поддержка отвечает быстро!»\n\n"
        "🌟 <b>Елена</b>: «Заказывала несколько товаров, всё пришло в течение минуты. Спасибо!»\n\n"
        "💬 Хотите оставить отзыв? Напишите нам в поддержку!"
    )
    
    # Кнопка для возврата в меню
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    
    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message, db: Database) -> None:
    """Обработчик кнопки '🆘 Поддержка'."""
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, вы можете:\n\n"
        "1️⃣ Написать в нашу службу поддержки\n"
        "2️⃣ Описать вашу проблему подробно\n"
        "3️⃣ Ожидать ответа в течение 5-10 минут\n\n"
        "📧 <b>Контакты:</b>\n"
        "• Email: support@cybermarket.com\n"
        "• Telegram: @CyberMarketSupport\n\n"
        "⏰ <b>Время работы:</b>\n"
        "• Ежедневно с 9:00 до 21:00 (МСК)"
    )
    
    # Кнопка для возврата в меню
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    
    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery, db: Database) -> None:
    """Обработчик кнопки '⬅️ В меню'."""
    await callback.answer()
    
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    try:
        await callback.message.edit_text(
            "👋 Вы вернулись в главное меню!\n"
            "Выберите действие:",
            reply_markup=main_menu(is_admin=is_admin)
        )
    except Exception:
        pass
