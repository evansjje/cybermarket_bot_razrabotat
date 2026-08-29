# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from database import db
from keyboards import main_menu

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral(message: Message) -> None:
    """Обработчик кнопки Рефералка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    # Создаем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Статистика:\n"
        f"• Приглашено друзей: 0\n"
        f"• Заработано: 0₽\n\n"
        f"Поделитесь ссылкой с друзьями и получайте "
        f"10% от их покупок!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔗 Поделиться', url=f"https://t.me/share/url?url={referral_link}")],
        [InlineKeyboardButton(text='⬅️ В меню', callback_data='back_to_menu')]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == '⭐ Отзывы')
async def reviews(message: Message) -> None:
    """Обработчик кнопки Отзывы"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    text = (
        f"⭐ <b>Отзывы наших клиентов</b>\n\n"
        f"🌟 <b>Алексей</b>: \"Отличный магазин! Всё работает, "
        f"рекомендую!\"\n\n"
        f"🌟 <b>Мария</b>: \"Быстрая доставка, качественный товар. "
        f"Спасибо!\"\n\n"
        f"🌟 <b>Дмитрий</b>: \"Лучший магазин цифровых товаров! "
        f"Всё чётко и быстро.\"\n\n"
        f"🌟 <b>Елена</b>: \"Пользуюсь уже месяц, всё отлично! "
        f"Поддержка всегда на связи.\"\n\n"
        f"💬 Хотите оставить отзыв? Напишите нам в поддержку!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ В меню', callback_data='back_to_menu')]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == '🆘 Поддержка')
async def support(message: Message) -> None:
    """Обработчик кнопки Поддержка"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    text = (
        f"🆘 <b>Служба поддержки</b>\n\n"
        f"Мы всегда готовы помочь вам!\n\n"
        f"📧 <b>Email:</b> support@cybermarket.ru\n"
        f"💬 <b>Telegram:</b> @cybermarket_support\n"
        f"🕐 <b>Время работы:</b> 24/7\n\n"
        f"Опишите вашу проблему, и мы ответим "
        f"в течение 15 минут!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📧 Написать в поддержку', url='https://t.me/cybermarket_support')],
        [InlineKeyboardButton(text='⬅️ В меню', callback_data='back_to_menu')]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback) -> None:
    """Возврат в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    try:
        await callback.message.edit_text(
            'Главное меню:',
            reply_markup=None
        )
    except Exception:
        pass
    
    await callback.message.answer(
        'Выберите раздел:',
        reply_markup=main_menu(is_admin=is_admin)
    )
