from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: Message, db: Database) -> None:
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    # Генерируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        "📊 Статистика:\n"
        "• Приглашено друзей: <b>0</b>\n"
        "• Заработано: <b>0 ₽</b>\n\n"
        "💡 Отправьте эту ссылку друзьям, и когда они "
        "зарегистрируются, вы получите бонус!"
    )
    
    await message.answer(text, reply_markup=main_menu(is_admin=is_admin))


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message, db: Database) -> None:
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    # Создаем клавиатуру с кнопкой для написания отзыва
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✍️ Написать отзыв",
            url="https://t.me/cybermarket_reviews"
        )
    )
    
    text = (
        "⭐ <b>Отзывы о магазине</b>\n\n"
        "🌟 <b>4.9/5</b> — средняя оценка наших клиентов\n\n"
        "💬 <b>Последние отзывы:</b>\n\n"
        "🟢 <b>Алексей</b>: \"Отличный магазин! Товар пришёл "
        "мгновенно, всё работает. Рекомендую!\"\n\n"
        "🟢 <b>Мария</b>: \"Быстрая поддержка, качественные "
        "товары. Уже не первый раз покупаю здесь!\"\n\n"
        "🟢 <b>Дмитрий</b>: \"Всё чётко, без обмана. Цены "
        "адекватные, товары рабочие. 10/10!\"\n\n"
        "👇 Хотите оставить отзыв? Нажмите на кнопку ниже!"
    )
    
    await message.answer(
        text,
        reply_markup=builder.as_markup()
    )


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message, db: Database) -> None:
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    # Создаем клавиатуру с кнопками связи
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📨 Написать в поддержку",
            url="https://t.me/cybermarket_support"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❓ Частые вопросы",
            callback_data="faq"
        )
    )
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Мы всегда готовы помочь вам!\n\n"
        "⏰ <b>Время работы:</b>\n"
        "• Пн-Пт: 9:00 - 21:00 (МСК)\n"
        "• Сб-Вс: 10:00 - 18:00 (МСК)\n\n"
        "📋 <b>Среднее время ответа:</b> ~15 минут\n\n"
        "Выберите удобный способ связи:"
    )
    
    await message.answer(
        text,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'faq')
async def faq_handler(callback: types.CallbackQuery) -> None:
    """Обработчик кнопки Частые вопросы"""
    await callback.answer()
    
    text = (
        "❓ <b>Частые вопросы</b>\n\n"
        "1️⃣ <b>Как получить товар после оплаты?</b>\n"
        "После оплаты товар автоматически отправляется вам "
        "в личные сообщения.\n\n"
        "2️⃣ <b>Какие способы оплаты доступны?</b>\n"
        "Мы принимаем оплату через СБП, криптовалюту и "
        "банковские карты.\n\n"
        "3️⃣ <b>Есть ли гарантия на товары?</b>\n"
        "Да, на все товары действует гарантия 30 дней.\n\n"
        "4️⃣ <b>Как быстро обрабатывается заказ?</b>\n"
        "Заказы обрабатываются мгновенно в автоматическом "
        "режиме.\n\n"
        "5️⃣ <b>Что делать, если товар не работает?</b>\n"
        "Напишите в поддержку, мы заменим товар или вернём "
        "деньги.\n\n"
        "Остались вопросы? Напишите в поддержку!"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardBuilder().row(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="back_to_support"
                )
            ).as_markup()
        )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_support')
async def back_to_support_handler(callback: types.CallbackQuery) -> None:
    """Возврат к меню поддержки"""
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📨 Написать в поддержку",
            url="https://t.me/cybermarket_support"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❓ Частые вопросы",
            callback_data="faq"
        )
    )
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Мы всегда готовы помочь вам!\n\n"
        "⏰ <b>Время работы:</b>\n"
        "• Пн-Пт: 9:00 - 21:00 (МСК)\n"
        "• Сб-Вс: 10:00 - 18:00 (МСК)\n\n"
        "📋 <b>Среднее время ответа:</b> ~15 минут\n\n"
        "Выберите удобный способ связи:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
    except Exception:
        pass
