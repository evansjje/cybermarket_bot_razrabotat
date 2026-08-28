from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import main_menu_kb
from config import settings

router = Router()


class OtherStates(StatesGroup):
    """Состояния для других разделов"""
    waiting_for_feedback = State()


@router.message(F.text == '👥 Рефералка')
async def referral_info(message: Message):
    """Показ реферальной информации"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте бонусы!\n\n"
        "🔗 Ваша реферальная ссылка:\n"
        f"<code>https://t.me/CyberMarket_Bot?start={user_id}</code>\n\n"
        "🎁 За каждого приглашенного друга вы получаете 5% от его первой покупки!\n\n"
        "📊 Статистика:\n"
        "• Приглашено друзей: 0\n"
        "• Заработано: 0₽\n\n"
        "Поделитесь ссылкой с друзьями и начните зарабатывать!",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews_info(message: Message):
    """Показ отзывов"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "⭐ <b>Отзывы наших клиентов</b>\n\n"
        "🌟 <b>Алексей</b>: «Отличный магазин! Товары приходят мгновенно, всё работает!»\n\n"
        "🌟 <b>Мария</b>: «Покупала подписку, всё чётко. Рекомендую!»\n\n"
        "🌟 <b>Дмитрий</b>: «Быстрая поддержка, качественные товары. 5 звёзд!»\n\n"
        "🌟 <b>Елена</b>: «Удобный бот, всё понятно. Спасибо за сервис!»\n\n"
        "🌟 <b>Игорь</b>: «Лучший магазин цифровых товаров! Всё на высшем уровне!»\n\n"
        "━━━━━━━━━━━━━━━\n"
        "Хотите оставить отзыв? Напишите нам в поддержку!",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.message(F.text == '🆘 Поддержка')
async def support_info(message: Message):
    """Показ информации о поддержке"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, мы всегда готовы помочь!\n\n"
        "📧 <b>Способы связи:</b>\n"
        "• 📱 Телеграм: @CyberMarket_Support\n"
        "• 📧 Email: support@cybermarket.com\n"
        "• 💬 Время работы: 24/7\n\n"
        "⚠️ <b>Частые вопросы:</b>\n"
        "• Как получить товар? — После оплаты товар приходит автоматически\n"
        "• Как вернуть деньги? — В течение 24 часов после покупки\n"
        "• Как связаться с поддержкой? — Напишите нам в любое время\n\n"
        "Нажмите на кнопку ниже, чтобы написать в поддержку:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    await callback.message.delete()
