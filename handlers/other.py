from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == "👥 Рефералка")
async def referral(message: Message, state: FSMContext, db: Database):
    """Обработчик кнопки Рефералка"""
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    # Формируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Получаем количество приглашенных пользователей
    invited_count = 0
    try:
        cursor = await db.db.execute(
            "SELECT COUNT(*) as count FROM users WHERE referred_by = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            invited_count = row["count"] if isinstance(row, dict) else row[0]
    except Exception:
        pass
    
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено друзей: <b>{invited_count}</b>\n\n"
        f"💰 За каждого приглашенного друга вы получаете <b>5%</b> от его первой покупки!\n\n"
        f"Поделитесь ссылкой с друзьями и зарабатывайте вместе с нами!",
        reply_markup=main_menu(user_id in settings.ADMIN_IDS)
    )


@router.message(F.text == "⭐ Отзывы")
async def reviews(message: Message, state: FSMContext, db: Database):
    """Обработчик кнопки Отзывы"""
    await state.clear()
    
    user_id = message.from_user.id
    
    await message.answer(
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 «Отличный магазин! Всё работает быстро и качественно» — Алексей\n\n"
        "🌟 «Пользуюсь услугами уже полгода, всё на высшем уровне» — Мария\n\n"
        "🌟 «Быстрая доставка товара, удобная оплата. Рекомендую!» — Дмитрий\n\n"
        "🌟 «Лучший магазин цифровых товаров, всегда есть в наличии» — Елена\n\n"
        "💬 Хотите оставить отзыв? Напишите нам в поддержку!",
        reply_markup=main_menu(user_id in settings.ADMIN_IDS)
    )


@router.message(F.text == "🆘 Поддержка")
async def support(message: Message, state: FSMContext, db: Database):
    """Обработчик кнопки Поддержка"""
    await state.clear()
    
    user_id = message.from_user.id
    
    await message.answer(
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, вы можете:\n\n"
        "1️⃣ Написать в нашу службу поддержки: @CyberMarketSupport\n\n"
        "2️⃣ Написать на почту: support@cybermarket.com\n\n"
        "3️⃣ Задать вопрос в нашем Telegram-канале: @CyberMarketNews\n\n"
        "⏰ Время работы поддержки: 24/7\n"
        "⚡️ Среднее время ответа: до 5 минут",
        reply_markup=main_menu(user_id in settings.ADMIN_IDS)
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, db: Database):
    """Возврат в главное меню"""
    await callback.answer()
    await state.clear()
    
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    try:
        await callback.message.edit_text(
            "🏠 Вы вернулись в главное меню.\n\n"
            "Выберите действие:",
            reply_markup=None
        )
    except Exception:
        pass
    
    await callback.message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu(is_admin)
    )
