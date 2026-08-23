# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database import get_cart_items, get_product, update_cart_item, clear_cart, get_cart_total
from keyboards import cart_kb, payment_kb

router = Router()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message) -> None:
    """Показать содержимое корзины"""
    user_id = message.from_user.id
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!\n\nДобавьте товары из каталога 🛍")
        return

    total = await get_cart_total(user_id)
    text = "🛒 <b>Ваша корзина:</b>\n\n"

    for item in cart_items:
        # item: (product_id, title, price, count)
        product_id, title, price, count = item
        text += f"📦 <b>{title}</b>\n"
        text += f"💰 Цена: {price} ₽\n"
        text += f"🔢 Количество: {count}\n"
        text += f"📊 Сумма: {price * count} ₽\n"
        text += "─────────────\n"

    text += f"\n<b>Итого: {total} ₽</b>"

    await message.answer(
        text,
        reply_markup=cart_kb()
    )


@router.callback_query(F.data.startswith("cart_inc_"))
async def increase_cart_item(callback: CallbackQuery) -> None:
    """Увеличить количество товара в корзине"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    await update_cart_item(user_id, product_id, 1)

    # Обновляем сообщение с корзиной
    await refresh_cart_message(callback)
    await callback.answer("✅ Количество увеличено")


@router.callback_query(F.data.startswith("cart_dec_"))
async def decrease_cart_item(callback: CallbackQuery) -> None:
    """Уменьшить количество товара в корзине"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    await update_cart_item(user_id, product_id, -1)

    # Обновляем сообщение с корзиной
    await refresh_cart_message(callback)
    await callback.answer("✅ Количество уменьшено")


@router.callback_query(F.data == "cart_clear")
async def clear_cart_handler(callback: CallbackQuery) -> None:
    """Очистить корзину"""
    user_id = callback.from_user.id

    await clear_cart(user_id)

    await callback.message.edit_text(
        "🗑 Корзина очищена!\n\n"
        "Добавьте новые товары из каталога 🛍"
    )
    await callback.answer("✅ Корзина очищена")


@router.callback_query(F.data == "cart_pay")
async def pay_cart(callback: CallbackQuery) -> None:
    """Оплатить корзину"""
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await callback.message.edit_text("🛒 Ваша корзина пуста!")
        await callback.answer()
        return

    total = await get_cart_total(user_id)

    text = (
        "💳 <b>Оформление заказа</b>\n\n"
        f"Сумма к оплате: <b>{total} ₽</b>\n\n"
        "Для оплаты напишите администратору:\n"
        "@admin_username\n\n"
        "После оплаты товар будет отправлен вам автоматически!"
    )

    await callback.message.edit_text(
        text,
        reply_markup=payment_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "cart_back")
async def back_to_cart(callback: CallbackQuery) -> None:
    """Вернуться к корзине"""
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\nДобавьте товары из каталога 🛍"
        )
        await callback.answer()
        return

    total = await get_cart_total(user_id)
    text = "🛒 <b>Ваша корзина:</b>\n\n"

    for item in cart_items:
        product_id, title, price, count = item
        text += f"📦 <b>{title}</b>\n"
        text += f"💰 Цена: {price} ₽\n"
        text += f"🔢 Количество: {count}\n"
        text += f"📊 Сумма: {price * count} ₽\n"
        text += "─────────────\n"

    text += f"\n<b>Итого: {total} ₽</b>"

    await callback.message.edit_text(
        text,
        reply_markup=cart_kb()
    )
    await callback.answer()


async def refresh_cart_message(callback: CallbackQuery) -> None:
    """Обновить сообщение с корзиной"""
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\nДобавьте товары из каталога 🛍"
        )
        return

    total = await get_cart_total(user_id)
    text = "🛒 <b>Ваша корзина:</b>\n\n"

    for item in cart_items:
        product_id, title, price, count = item
        text += f"📦 <b>{title}</b>\n"
        text += f"💰 Цена: {price} ₽\n"
        text += f"🔢 Количество: {count}\n"
        text += f"📊 Сумма: {price * count} ₽\n"
        text += "─────────────\n"

    text += f"\n<b>Итого: {total} ₽</b>"

    try:
        await callback.message.edit_text(
            text,
            reply_markup=cart_kb()
        )
    except TelegramBadRequest:
        pass
