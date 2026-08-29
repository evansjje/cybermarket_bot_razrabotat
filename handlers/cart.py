# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message) -> None:
    """Показ корзины пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        await message.answer('🛒 Ваша корзина пуста')
        return

    text = '🛒 <b>Ваша корзина:</b>\n\n'
    total = 0

    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_total = price * count
        total += item_total
        text += f"📦 {title}\n"
        text += f"💰 {price}₽ x {count} = <b>{item_total}₽</b>\n\n"

    text += f"━━━━━━━━━━━━━\n"
    text += f"<b>Итого: {total}₽</b>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')],
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='checkout')]
    ])

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery) -> None:
    """Очистка корзины"""
    await callback.answer()
    user_id = callback.from_user.id
    await db.clear_cart(user_id)

    try:
        await callback.message.edit_text('🗑 Корзина очищена')
    except Exception:
        pass


@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery) -> None:
    """Оформление заказа"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        try:
            await callback.message.edit_text('🛒 Ваша корзина пуста')
        except Exception:
            pass
        return

    total = sum(
        item.get('price', 0) * item.get('count', 1)
        for item in cart_items
    )

    text = (
        f"💳 <b>Оформление заказа</b>\n\n"
        f"Сумма к оплате: <b>{total}₽</b>\n\n"
        f"Для оплаты свяжитесь с поддержкой: @support"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Назад в корзину', callback_data='back_to_cart')]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_cart')
async def back_to_cart(callback: CallbackQuery) -> None:
    """Возврат к корзине"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        try:
            await callback.message.edit_text('🛒 Ваша корзина пуста')
        except Exception:
            pass
        return

    text = '🛒 <b>Ваша корзина:</b>\n\n'
    total = 0

    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_total = price * count
        total += item_total
        text += f"📦 {title}\n"
        text += f"💰 {price}₽ x {count} = <b>{item_total}₽</b>\n\n"

    text += f"━━━━━━━━━━━━━\n"
    text += f"<b>Итого: {total}₽</b>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')],
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='checkout')]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass
