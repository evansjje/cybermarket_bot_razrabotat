from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import add_user, get_user, get_referral_count, get_referral_earnings
from keyboards import main_menu_keyboard, referral_keyboard, reviews_keyboard, support_keyboard

router = Router()


@router.message(F.text == "👥 Рефералка")
async def show_referral(message: Message):
    """Показать реферальную информацию"""
    user_id = message.from_user.id
    username = message.from_user.username or "user"
    
    # Реферальная ссылка
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Статистика
    referral_count = await get_referral_count(user_id)
    referral_earnings = await get_referral_earnings(user_id)
    
    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено друзей: <b>{referral_count}</b>\n"
        f"💰 Заработано: <b>{referral_earnings} ₽</b>\n\n"
        f"За каждого приглашенного друга вы получаете <b>10%</b> от его первой покупки!"
    )
    
    await message.answer(
        text,
        reply_markup=referral_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    """Показать отзывы"""
    text = (
        f"⭐ <b>Отзывы наших клиентов</b>\n\n"
        f"🌟 <b>Алексей</b>: \"Отличный магазин! Купил скрипт для парсинга, всё работает идеально. Рекомендую!\"\n\n"
        f"🌟 <b>Мария</b>: \"Курс по Python просто огонь! Всё понятно и структурировано. Спасибо!\"\n\n"
        f"🌟 <b>Дмитрий</b>: \"Быстрая доставка товара, качественный софт. Буду заказывать ещё!\"\n\n"
        f"🌟 <b>Елена</b>: \"Отличная поддержка, помогли с установкой. Магазин супер!\"\n\n"
        f"🌟 <b>Игорь</b>: \"Пользуюсь вашими скриптами уже месяц, всё стабильно работает. Спасибо!\"\n\n"
        f"Хотите оставить отзыв? Напишите нам в поддержку!"
    )
    
    await message.answer(
        text,
        reply_markup=reviews_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "🆘 Поддержка")
async def show_support(message: Message):
    """Показать информацию о поддержке"""
    text = (
        f"🆘 <b>Поддержка CyberMarket</b>\n\n"
        f"Мы всегда готовы помочь вам!\n\n"
        f"📧 <b>Email:</b> support@cybermarket.ru\n"
        f"💬 <b>Telegram:</b> @CyberMarketSupport\n"
        f"🌐 <b>Сайт:</b> cybermarket.ru\n\n"
        f"⏰ <b>Время работы:</b>\n"
        f"Пн-Пт: 9:00 - 21:00 (МСК)\n"
        f"Сб-Вс: 10:00 - 18:00 (МСК)\n\n"
        f"Среднее время ответа: <b>до 30 минут</b>"
    )
    
    await message.answer(
        text,
        reply_markup=support_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "👋 Добро пожаловать в CyberMarket!\n\n"
        "Здесь вы можете приобрести цифровые товары: скрипты, курсы и софт.\n"
        "Используйте кнопки ниже для навигации:",
        reply_markup=main_menu_keyboard(user_id)
    )
    await callback.answer()
