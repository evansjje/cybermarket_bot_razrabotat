from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import Database
from config import settings

router = Router()
db = Database()


@router.message(F.text == '👥 Рефералка')
async def referral_system(message: Message):
    """Показать реферальную информацию"""
    user_id = message.from_user.id
    referral_count = await db.get_referrals_count(user_id)
    
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено пользователей: <b>{referral_count}</b>\n\n"
        f"Поделитесь этой ссылкой с друзьями и получайте бонусы!"
    )
    
    await message.answer(text)


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message):
    """Показать информацию об отзывах"""
    text = (
        f"⭐ <b>Отзывы о CyberMarket</b>\n\n"
        f"💬 Наши клиенты высоко оценивают качество товаров и скорость доставки!\n\n"
        f"📝 Хотите оставить отзыв? Напишите нам в поддержку:\n"
        f"🆘 <b>Поддержка</b> - в главном меню\n\n"
        f"🌟 Средняя оценка: 4.9/5\n"
        f"👥 Более 1000 довольных клиентов"
    )
    
    await message.answer(text)


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message):
    """Показать контакты поддержки"""
    text = (
        f"🆘 <b>Поддержка CyberMarket</b>\n\n"
        f"📧 Email: support@cybermarket.com\n"
        f"💬 Telegram: @cybermarket_support\n"
        f"🕐 Время работы: 24/7\n\n"
        f"Опишите вашу проблему, и мы поможем в ближайшее время!"
    )
    
    await message.answer(text)


async def reviews(callback: CallbackQuery):
    """Обработчик отзывов для callback-запросов"""
    await callback.answer("⭐ Отзывы о CyberMarket", show_alert=True)
    text = (
        f"⭐ <b>Отзывы о CyberMarket</b>\n\n"
        f"💬 Наши клиенты высоко оценивают качество товаров и скорость доставки!\n\n"
        f"📝 Хотите оставить отзыв? Напишите нам в поддержку:\n"
        f"🆘 <b>Поддержка</b> - в главном меню\n\n"
        f"🌟 Средняя оценка: 4.9/5\n"
        f"👥 Более 1000 довольных клиентов"
    )
    await callback.message.answer(text)


async def support(callback: CallbackQuery):
    """Обработчик поддержки для callback-запросов"""
    await callback.answer("🆘 Поддержка CyberMarket", show_alert=True)
    text = (
        f"🆘 <b>Поддержка CyberMarket</b>\n\n"
        f"📧 Email: support@cybermarket.com\n"
        f"💬 Telegram: @cybermarket_support\n"
        f"🕐 Время работы: 24/7\n\n"
        f"Опишите вашу проблему, и мы поможем в ближайшее время!"
    )
    await callback.message.answer(text)
