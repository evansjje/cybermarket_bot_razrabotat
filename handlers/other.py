from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards import main_menu
from config import settings

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_system(message: Message, db: Database) -> None:
    """Показывает реферальную систему"""
    user_id = message.from_user.id
    
    # Получаем количество рефералов
    referrals_count = await db.get_referrals_count(user_id)
    
    # Генерируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено пользователей: <b>{referrals_count}</b>\n\n"
        f"💡 Отправьте эту ссылку друзьям, и когда они перейдут по ней, "
        f"вы получите бонусы!"
    )
    
    await message.answer(text)


@router.message(F.text == '⭐ Отзывы')
async def show_reviews(message: Message) -> None:
    """Показывает отзывы о магазине"""
    text = (
        "⭐ <b>Отзывы наших клиентов:</b>\n\n"
        "🌟 «Отличный магазин! Всё пришло мгновенно, товар качественный.» — Иван\n\n"
        "🌟 «Быстрая доставка и отличная поддержка. Рекомендую!» — Мария\n\n"
        "🌟 «Удобный интерфейс, понятные цены. Всё на высшем уровне!» — Алексей\n\n"
        "💬 Хотите оставить отзыв? Напишите нам в поддержку!"
    )
    
    await message.answer(text)


@router.message(F.text == '🆘 Поддержка')
async def show_support(message: Message) -> None:
    """Показывает контакты поддержки"""
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, обратитесь к нам:\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @cybermarket_support\n"
        "🕐 Время работы: 24/7\n\n"
        "Мы всегда рады помочь!"
    )
    
    await message.answer(text)


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database) -> None:
    """Возвращает в главное меню"""
    from config import settings
    is_admin = message.from_user.id in settings.ADMIN_IDS
    
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin=is_admin)
    )
