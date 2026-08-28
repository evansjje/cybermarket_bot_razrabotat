from aiogram import Router, types, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import main_menu
from config import settings
import random
import string

router = Router()


def generate_referral_code(user_id: int) -> str:
    """Генерация реферального кода"""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{user_id}{random_part}"


@router.message(F.text == "👥 Рефералка")
async def referral_system(message: Message, db: Database) -> None:
    """Реферальная система"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден. Нажмите /start")
        return
    
    # Генерируем реферальный код, если его нет
    if not user.get('referral_code'):
        referral_code = generate_referral_code(user_id)
        await db.update_user_referral_code(user_id, referral_code)
    else:
        referral_code = user['referral_code']
    
    # Считаем количество рефералов
    referrals_count = await db.get_referrals_count(user_id)
    
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"
    
    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено пользователей: <b>{referrals_count}</b>\n\n"
        f"Поделитесь этой ссылкой с друзьями и получайте бонусы!"
    )
    
    await message.answer(text, reply_markup=main_menu())


@router.message(F.text == "⭐ Отзывы")
async def reviews(message: Message) -> None:
    """Отзывы о магазине"""
    text = (
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 <b>Алексей</b>: «Отличный магазин! Товар пришел мгновенно, все работает. Рекомендую!»\n\n"
        "🌟 <b>Мария</b>: «Быстрая поддержка, качественные товары. Уже не первый раз покупаю здесь!»\n\n"
        "🌟 <b>Дмитрий</b>: «Лучший магазин цифровых товаров! Всё четко и без обмана.»\n\n"
        "🌟 <b>Елена</b>: «Удобный интерфейс, понятные цены. Покупка заняла меньше минуты!»\n\n"
        "🌟 <b>Игорь</b>: «Рекомендую всем! Товары соответствуют описанию, поддержка на высоте.»\n\n"
        "Хотите оставить свой отзыв? Напишите нам в поддержку!"
    )
    
    await message.answer(text, reply_markup=main_menu())


@router.message(F.text == "🆘 Поддержка")
async def support(message: Message) -> None:
    """Контакты поддержки"""
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, вы можете связаться с нами:\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @CyberMarketSupport\n"
        "🕐 Время работы: 24/7\n\n"
        "Мы ответим вам в ближайшее время!"
    )
    
    await message.answer(text, reply_markup=main_menu())


@router.message(F.text.startswith("/start ref_"))
async def referral_start(message: Message, db: Database) -> None:
    """Обработка перехода по реферальной ссылке"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Получаем реферальный код из команды
    referral_code = message.text.split("ref_")[1]
    
    # Ищем пользователя, который пригласил
    referrer = await db.get_user_by_referral_code(referral_code)
    
    # Проверяем, есть ли пользователь в БД
    existing_user = await db.get_user(user_id)
    if not existing_user:
        # Создаем нового пользователя с реферальным кодом
        await db.add_user(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            referred_by=referrer['id'] if referrer else None
        )
        
        # Генерируем собственный реферальный код
        new_referral_code = generate_referral_code(user_id)
        await db.update_user_referral_code(user_id, new_referral_code)
        
        if referrer:
            await message.answer(
                f"🎉 Вы перешли по реферальной ссылке!\n"
                f"Вам начислен бонус за регистрацию!"
            )
    else:
        await message.answer("👋 С возвращением!")
    
    # Отправляем приветственное сообщение и главное меню
    await message.answer(
        f"👋 Добро пожаловать, {first_name or 'пользователь'}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите раздел в меню ниже:",
        reply_markup=main_menu()
    )
