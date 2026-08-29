from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import main_menu

router = Router()
db = Database()


@router.message(F.text == '👥 Рефералка')
async def referral_system(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    # Ссылка на бота с реферальным кодом
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    # Получаем количество рефералов
    referrals_count = await db.get_referrals_count(user_id)
    
    text = (
        f"👥 Реферальная система\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"{referral_link}\n\n"
        f"📊 Приглашено пользователей: {referrals_count}\n\n"
        f"💡 Отправьте эту ссылку друзьям, и когда они перейдут по ней, "
        f"они станут вашими рефералами!"
    )
    
    await message.answer(text)


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message, state: FSMContext):
    await state.clear()
    
    text = (
        "⭐ Отзывы о нашем магазине\n\n"
        "🌟 Мы гордимся качеством наших товаров и сервиса!\n\n"
        "📝 Хотите оставить отзыв? Напишите нам в поддержку:\n"
        "@CyberMarket_Support\n\n"
        "💬 Ваше мнение очень важно для нас!"
    )
    
    await message.answer(text)


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message, state: FSMContext):
    await state.clear()
    
    text = (
        "🆘 Поддержка CyberMarket\n\n"
        "📧 Свяжитесь с нами:\n"
        "📩 Email: support@cybermarket.com\n"
        "💬 Telegram: @CyberMarket_Support\n\n"
        "🕐 Время работы: 24/7\n\n"
        "⚡️ Мы ответим на все ваши вопросы в ближайшее время!"
    )
    
    await message.answer(text)
