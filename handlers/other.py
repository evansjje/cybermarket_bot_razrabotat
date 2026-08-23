# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import main_menu_kb, back_to_menu_kb
from config import settings

router = Router()
db = Database()


class SupportStates(StatesGroup):
    """Состояния для поддержки."""
    waiting_message = State()


@router.message(F.text == "⭐ Отзывы")
async def reviews_handler(message: Message):
    """Показать отзывы о магазине."""
    await message.answer(
        "⭐ <b>Отзывы наших клиентов:</b>\n\n"
        "🌟 «Отличный магазин! Всё работает, товар пришёл мгновенно» — Алексей\n"
        "🌟 «Быстрая поддержка, качественные товары. Рекомендую!» — Мария\n"
        "🌟 «Покупаю здесь постоянно, всё на высшем уровне» — Дмитрий\n\n"
        "Хотите оставить отзыв? Напишите его в чат, и мы обязательно его опубликуем!",
        parse_mode="HTML"
    )


@router.message(F.text == "🆘 Поддержка")
async def support_handler(message: Message, state: FSMContext):
    """Начать диалог с поддержкой."""
    await message.answer(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Опишите вашу проблему или вопрос, и мы ответим вам в ближайшее время.\n\n"
        "Напишите ваше сообщение:",
        parse_mode="HTML"
    )
    await state.set_state(SupportStates.waiting_message)


@router.message(SupportStates.waiting_message)
async def support_message_handler(message: Message, state: FSMContext):
    """Обработка сообщения в поддержку."""
    user_id = message.from_user.id
    username = message.from_user.username or "нет username"
    text = message.text

    # Здесь можно добавить отправку сообщения админу
    # Например, через бота или email
    
    await message.answer(
        "✅ Ваше сообщение отправлено в поддержку!\n\n"
        "Мы ответим вам в ближайшее время. Спасибо за обращение!",
        reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
    )
    await state.clear()


@router.message(F.text == "👥 Рефералка")
async def referral_handler(message: Message):
    """Показать реферальную программу."""
    user_id = message.from_user.id
    referral_code = f"REF{user_id}"
    
    # Проверяем, есть ли у пользователя реферальный код
    user = await db.get_user(user_id)
    if user and user.get("referral_code"):
        referral_code = user["referral_code"]
    
    # Получаем количество приглашённых
    referrals_count = await db.get_referrals_count(user_id)
    
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        f"Ваш реферальный код: <code>{referral_code}</code>\n\n"
        f"Приглашено друзей: {referrals_count}\n\n"
        "🎁 <b>Как это работает:</b>\n"
        "1. Поделитесь вашим реферальным кодом с друзьями\n"
        "2. Друг вводит ваш код при регистрации\n"
        "3. Вы получаете бонусы на счёт\n\n"
        "📎 Ваша реферальная ссылка:\n"
        f"<code>https://t.me/CyberMarketBot?start={referral_code}</code>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню."""
    await state.clear()
    user_id = callback.from_user.id
    is_admin = (user_id == settings.ADMIN_ID)
    
    await callback.message.delete()
    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите раздел:",
        reply_markup=main_menu_kb(is_admin=is_admin),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(F.text == "🔙 В меню")
async def back_to_menu_handler(message: Message, state: FSMContext):
    """Вернуться в главное меню."""
    await state.clear()
    user_id = message.from_user.id
    is_admin = (user_id == settings.ADMIN_ID)
    
    await message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите раздел:",
        reply_markup=main_menu_kb(is_admin=is_admin),
        parse_mode="HTML"
    )


async def show_support(message: Message, state: FSMContext):
    """Показать меню поддержки."""
    await message.answer(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Опишите вашу проблему или вопрос, и мы ответим вам в ближайшее время.\n\n"
        "Напишите ваше сообщение:",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb()
    )
    await state.set_state(SupportStates.waiting_message)


async def referral_program(message: Message):
    """Показать реферальную программу."""
    user_id = message.from_user.id
    referral_code = f"REF{user_id}"
    
    user = await db.get_user(user_id)
    if user and user.get("referral_code"):
        referral_code = user["referral_code"]
    
    referrals_count = await db.get_referrals_count(user_id)
    
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        f"Ваш реферальный код: <code>{referral_code}</code>\n\n"
        f"Приглашено друзей: {referrals_count}\n\n"
        "🎁 <b>Как это работает:</b>\n"
        "1. Поделитесь вашим реферальным кодом с друзьями\n"
        "2. Друг вводит ваш код при регистрации\n"
        "3. Вы получаете бонусы на счёт\n\n"
        "📎 Ваша реферальная ссылка:\n"
        f"<code>https://t.me/CyberMarketBot?start={referral_code}</code>",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb()
    )


async def show_reviews(message: Message):
    """Показать отзывы о магазине."""
    await message.answer(
        "⭐ <b>Отзывы наших клиентов:</b>\n\n"
        "🌟 «Отличный магазин! Всё работает, товар пришёл мгновенно» — Алексей\n"
        "🌟 «Быстрая поддержка, качественные товары. Рекомендую!» — Мария\n"
        "🌟 «Покупаю здесь постоянно, всё на высшем уровне» — Дмитрий\n\n"
        "Хотите оставить отзыв? Напишите его в чат, и мы обязательно его опубликуем!",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb()
    )
