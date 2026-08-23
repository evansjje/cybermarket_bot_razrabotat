# handlers/other.py
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from urllib.parse import quote

from database import Database
from keyboards import main_menu_kb
from config import settings

router = Router()
db = Database()


@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    """Показать отзывы о магазине"""
    user_id = message.from_user.id
    is_admin = user_id == settings.ADMIN_ID

    reviews_text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 <b>Иван</b>: «Отличный магазин! Всё работает, товар пришёл мгновенно. Рекомендую!»\n\n"
        "🌟 <b>Мария</b>: «Купила курс по Python, всё чётко и без обмана. Спасибо!»\n\n"
        "🌟 <b>Дмитрий</b>: «Быстрая поддержка, качественные товары. 10/10!»\n\n"
        "🌟 <b>Анна</b>: «Пользуюсь сервисом уже месяц, всё на высшем уровне!»\n\n"
        "🌟 <b>Сергей</b>: «Лучший магазин цифровых товаров, который я находил!»\n\n"
        "─────────────\n"
        "💬 Хотите оставить отзыв? Напишите нам в поддержку!"
    )

    await message.answer(
        reviews_text,
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.message(F.text == "🆘 Поддержка")
async def show_support(message: Message):
    """Показать контакты поддержки"""
    user_id = message.from_user.id
    is_admin = user_id == settings.ADMIN_ID

    support_text = (
        "🆘 <b>Поддержка CyberMarket</b>\n\n"
        "Мы всегда готовы помочь вам!\n\n"
        "📧 <b>Email:</b> support@cybermarket.ru\n"
        "💬 <b>Telegram:</b> @CyberMarketSupport\n"
        "🌐 <b>Сайт:</b> cybermarket.ru\n\n"
        "⏰ <b>Время работы:</b>\n"
        "Ежедневно с 10:00 до 22:00 (МСК)\n\n"
        "📝 <b>Часто задаваемые вопросы:</b>\n"
        "1️⃣ Как получить товар после оплаты?\n"
        "   → Товар приходит автоматически в чат после оплаты\n\n"
        "2️⃣ Что делать, если товар не пришёл?\n"
        "   → Напишите в поддержку, мы решим проблему в течение 15 минут\n\n"
        "3️⃣ Можно ли вернуть деньги?\n"
        "   → Да, если товар не соответствует описанию"
    )

    await message.answer(
        support_text,
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.message(F.text == "👥 Рефералка")
async def show_referral(message: Message):
    """Показать реферальную программу"""
    user_id = message.from_user.id
    is_admin = user_id == settings.ADMIN_ID

    # Получаем реферальный код пользователя
    user = await db.get_user(user_id)
    referral_code = user.get('referral_code') if user else None

    if not referral_code:
        # Генерируем реферальный код
        import random
        import string
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        await db.update_referral_code(user_id, referral_code)

    # Считаем рефералов
    referrals_count = await db.get_referrals_count(user_id)

    # Формируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"

    referral_text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "🎁 <b>Приглашайте друзей и получайте бонусы!</b>\n\n"
        "💰 <b>Условия:</b>\n"
        "• За каждого приглашённого друга вы получаете <b>10%</b> от его первой покупки\n"
        "• Друг получает <b>скидку 5%</b> на первый заказ\n\n"
        f"📊 <b>Ваша статистика:</b>\n"
        f"• Приглашено друзей: <b>{referrals_count}</b>\n"
        f"• Ваш реферальный код: <code>{referral_code}</code>\n\n"
        "🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        "📋 <b>Как это работает:</b>\n"
        "1. Отправьте ссылку другу\n"
        "2. Друг переходит по ссылке и регистрируется\n"
        "3. Вы получаете бонус после его первой покупки\n\n"
        "💡 <b>Совет:</b> Поделитесь ссылкой в соцсетях и чатах!"
    )

    # Создаем клавиатуру с кнопкой копирования
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy_referral")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

    await message.answer(
        referral_text,
        reply_markup=kb
    )


@router.callback_query(F.data == "copy_referral")
async def copy_referral(callback: CallbackQuery):
    """Обработка копирования реферальной ссылки"""
    user_id = callback.from_user.id
    
    # Получаем реферальный код
    user = await db.get_user(user_id)
    referral_code = user.get('referral_code') if user else None

    if not referral_code:
        import random
        import string
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        await db.update_referral_code(user_id, referral_code)

    bot_username = (await callback.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"

    await callback.answer(
        f"Ссылка скопирована: {referral_link}",
        show_alert=True
    )


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    is_admin = user_id == settings.ADMIN_ID

    await callback.message.delete()
    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    await callback.answer()


@router.message(Command("help"))
async def show_help(message: Message):
    """Показать справку по командам"""
    user_id = message.from_user.id
    is_admin = user_id == settings.ADMIN_ID

    help_text = (
        "📚 <b>Справка по командам</b>\n\n"
        "🛍 <b>Каталог</b> — просмотр категорий и товаров\n"
        "🛒 <b>Корзина</b> — просмотр и управление корзиной\n"
        "👥 <b>Рефералка</b> — реферальная программа\n"
        "⭐ <b>Отзывы</b> — отзывы о магазине\n"
        "🆘 <b>Поддержка</b> — контакты поддержки\n\n"
        "📌 <b>Команды:</b>\n"
        "/start — начать работу с ботом\n"
        "/help — показать эту справку\n"
    )

    if is_admin:
        help_text += "/admin — открыть админ-панель\n"

    await message.answer(
        help_text,
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.message()
async def handle_unknown(message: Message):
    """Обработка неизвестных сообщений"""
    user_id = message.from_user.id
    is_admin = user_id == settings.ADMIN_ID

    await message.answer(
        "🤔 Я не понимаю эту команду.\n\n"
        "Используйте кнопки меню или команду /help для получения справки.",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
