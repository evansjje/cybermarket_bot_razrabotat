# handlers/cart.py
from aiogram import Router, types, F
from database import Database
from keyboards import get_main_menu
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from contextlib import suppress

router = Router()
db = Database()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: types.Message):
    """Показ корзины пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Перейдите в 🛍 Каталог, чтобы выбрать товары.",
            reply_markup=get_main_menu(is_admin=user_id in [])
        )
        return

    # Формируем текст корзины
    text = "🛒 Ваша корзина:\n\n"
    total = 0.0

    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_total = price * count
        total += item_total
        text += f"• {title} — {price}₽ × {count} = {item_total}₽\n"

    text += f"\n💰 Итого: {total}₽"

    # Клавиатура с кнопками очистки и оплаты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart'),
            InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart')
        ],
        [
            InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')
        ]
    ])

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'clear_cart')
async def clear_cart_callback(callback: types.CallbackQuery):
    """Очистка корзины"""
    await callback.answer()

    user_id = callback.from_user.id
    await db.clear_cart(user_id)

    with suppress(Exception):
        await callback.message.edit_text(
            "🗑 Корзина очищена!",
            reply_markup=None
        )


@router.callback_query(F.data == 'pay_cart')
async def pay_cart_callback(callback: types.CallbackQuery):
    """Оплата корзины"""
    await callback.answer()

    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        with suppress(Exception):
            await callback.message.edit_text(
                "❌ Корзина пуста!",
                reply_markup=None
            )
        return

    total = sum(item.get('price', 0) * item.get('count', 1) for item in cart_items)

    # Здесь можно добавить интеграцию с платёжной системой
    with suppress(Exception):
        await callback.message.edit_text(
            f"💳 Оплата на сумму {total}₽\n\n"
            "🔒 Оплата в разработке. Свяжитесь с поддержкой для оплаты.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
            ])
        )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu_callback(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()

    user_id = callback.from_user.id
    is_admin = user_id in []  # Здесь нужно передать settings.ADMIN_IDS

    with suppress(Exception):
        await callback.message.edit_text(
            "🏠 Главное меню",
            reply_markup=None
        )
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu(is_admin=is_admin)
        )
