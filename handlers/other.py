from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: Message):
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    # Формируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        "📊 Статистика:\n"
        f"👤 Приглашено друзей: <b>{await db.get_referrals_count(user_id)}</b>\n\n"
        "💡 За каждого приглашенного друга вы получаете бонус!"
    )
    
    await message.answer(text, reply_markup=main_menu(is_admin=is_admin))


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message):
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 <b>Алексей:</b> \"Отличный магазин! Всё работает быстро и качественно.\"\n\n"
        "🌟 <b>Мария:</b> \"Лучший бот для покупки цифровых товаров. Рекомендую!\"\n\n"
        "🌟 <b>Дмитрий:</b> \"Быстрая доставка, отличная поддержка. 10/10!\"\n\n"
        "🌟 <b>Елена:</b> \"Пользуюсь уже месяц, всё на высшем уровне!\"\n\n"
        "💬 Хотите оставить отзыв? Напишите в поддержку!"
    )
    
    await message.answer(text, reply_markup=main_menu(is_admin=is_admin))


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message):
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, мы всегда готовы помочь!\n\n"
        "📝 <b>Частые вопросы:</b>\n"
        "• Как получить товар после оплаты?\n"
        "• Как работает реферальная программа?\n"
        "• Как связаться с администратором?\n\n"
        "💬 Для связи с поддержкой напишите:\n"
        "👤 @support_username\n"
        "📧 support@cybermarket.com\n\n"
        "⏰ Время работы: 24/7"
    )
    
    await message.answer(text, reply_markup=main_menu(is_admin=is_admin))


@router.callback_query(F.data.startswith('ref_'))
async def referral_callback(callback: CallbackQuery):
    """Обработчик реферальной ссылки"""
    await callback.answer()
    
    # Получаем ID пригласившего
    referrer_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    if referrer_id != user_id:
        # Регистрируем реферала
        await db.db.execute(
            "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
            (referrer_id, user_id)
        )
        await db.db.commit()
    
    # Отправляем приветствие
    await callback.message.answer(
        "👋 Добро пожаловать в CyberMarket!\n\n"
        "🛍 Выберите раздел меню:",
        reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
    )
