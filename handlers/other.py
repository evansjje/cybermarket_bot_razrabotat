from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: Message, db: Database):
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    # Генерируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        "📊 <b>Как это работает:</b>\n"
        "• Друг переходит по вашей ссылке\n"
        "• Регистрируется в боте\n"
        "• Вы получаете бонус на счет\n\n"
        "💡 Отправьте эту ссылку друзьям и зарабатывайте!",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message, db: Database):
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 <b>Алексей:</b> \"Отличный магазин! Всё пришло мгновенно, товар качественный. Рекомендую!\"\n\n"
        "🌟 <b>Мария:</b> \"Покупала ключ для игры - всё работает. Поддержка отвечает быстро. 10/10!\"\n\n"
        "🌟 <b>Дмитрий:</b> \"Удобный бот, быстрая оплата. Уже 3-я покупка, всё на высшем уровне!\"\n\n"
        "🌟 <b>Елена:</b> \"Отличный выбор цифровых товаров. Цены радуют, оформление за 2 минуты!\"\n\n"
        "💬 Хотите оставить отзыв? Напишите в поддержку!",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message, db: Database):
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Мы всегда готовы помочь вам!\n\n"
        "📝 <b>Частые вопросы:</b>\n"
        "• Как получить товар? — После оплаты товар придёт в личные сообщения\n"
        "• Как оплатить? — Оплата через платежную систему в боте\n"
        "• Не пришёл товар? — Напишите нам, решим в течение 5 минут\n\n"
        "📬 <b>Связаться с нами:</b>\n"
        "• Напишите @support_username\n"
        "• Или используйте команду /support\n\n"
        "⏰ Время работы: круглосуточно",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(Command('support'))
async def support_command(message: Message, db: Database):
    """Обработчик команды /support"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Мы всегда готовы помочь вам!\n\n"
        "📝 <b>Частые вопросы:</b>\n"
        "• Как получить товар? — После оплаты товар придёт в личные сообщения\n"
        "• Как оплатить? — Оплата через платежную систему в боте\n"
        "• Не пришёл товар? — Напишите нам, решим в течение 5 минут\n\n"
        "📬 <b>Связаться с нами:</b>\n"
        "• Напишите @support_username\n"
        "• Или используйте команду /support\n\n"
        "⏰ Время работы: круглосуточно",
        reply_markup=main_menu(is_admin=is_admin)
    )
