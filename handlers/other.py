from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_system(message: Message, db: Database):
    """Показать реферальную ссылку пользователя"""
    user_id = message.from_user.id
    username = message.from_user.username

    # Генерируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    # Получаем количество рефералов
    referrals_count = await db.get_referrals_count(user_id)

    # Получаем информацию о пользователе
    user = await db.get_user(user_id)

    is_admin = user_id in settings.ADMIN_IDS

    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Ваши рефералы: {referrals_count}\n\n"
        f"💡 Приглашайте друзей по вашей ссылке и получайте бонусы!"
    )

    await message.answer(text, reply_markup=main_menu(is_admin))


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message, db: Database):
    """Показать отзывы о магазине"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    text = (
        "⭐ <b>Отзывы о CyberMarket</b>\n\n"
        "🌟 <b>Отличный магазин!</b>\n"
        "Быстрая доставка товаров, всё работает как описано. Рекомендую!\n"
        "— <i>Алексей</i>\n\n"
        "🌟 <b>Лучший выбор цифровых товаров</b>\n"
        "Огромный ассортимент, приятные цены. Покупкой доволен!\n"
        "— <i>Мария</i>\n\n"
        "🌟 <b>Надёжно и качественно</b>\n"
        "Уже не первый раз покупаю здесь. Всё на высшем уровне!\n"
        "— <i>Дмитрий</i>\n\n"
        "💬 Хотите оставить отзыв? Напишите нам в поддержку!"
    )

    await message.answer(text, reply_markup=main_menu(is_admin))


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message, db: Database):
    """Показать контакты поддержки"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    text = (
        "🆘 <b>Поддержка CyberMarket</b>\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @cybermarket_support\n"
        "🕐 Время работы: 24/7\n\n"
        "📝 Опишите вашу проблему, и мы постараемся помочь в кратчайшие сроки!"
    )

    await message.answer(text, reply_markup=main_menu(is_admin))


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database):
    """Вернуться в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        "Вы вернулись в главное меню",
        reply_markup=main_menu(is_admin)
    )
