from aiogram import Router, F
from aiogram.types import Message
from keyboards import main_menu_kb

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: Message):
    user_id = message.from_user.id
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашай друзей и получай бонусы!\n\n"
        f"🔗 Твоя реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        "Отправь эту ссылку друзьям — когда они перейдут по ней и начнут пользоваться ботом, ты получишь награду!"
    )
    
    await message.answer(text, reply_markup=main_menu_kb(user_id))


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message):
    user_id = message.from_user.id
    
    text = (
        "⭐ <b>Отзывы о CyberMarket</b>\n\n"
        "🌟 <b>4.9/5</b> — средняя оценка наших клиентов\n\n"
        "💬 <b>Что говорят покупатели:</b>\n\n"
        "«Отличный магазин! Всё пришло мгновенно, качество на высоте!» — Иван\n\n"
        "«Лучший бот для покупки цифровых товаров. Рекомендую!» — Мария\n\n"
        "«Быстро, удобно, надёжно. Уже не первый раз покупаю здесь» — Алексей\n\n"
        "Хочешь оставить свой отзыв? Напиши нам в поддержку!"
    )
    
    await message.answer(text, reply_markup=main_menu_kb(user_id))


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message):
    user_id = message.from_user.id
    
    text = (
        "🆘 <b>Поддержка CyberMarket</b>\n\n"
        "Мы всегда готовы помочь тебе!\n\n"
        "📧 <b>Email:</b> support@cybermarket.shop\n"
        "💬 <b>Telegram:</b> @CyberMarketSupport\n"
        "⏰ <b>Время работы:</b> 24/7\n\n"
        "Опиши свою проблему — и мы ответим в ближайшее время!"
    )
    
    await message.answer(text, reply_markup=main_menu_kb(user_id))
