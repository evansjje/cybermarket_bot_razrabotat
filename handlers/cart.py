# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_cart, clear_cart, get_product
from keyboards import main_menu_kb, cart_kb

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message) -> None:
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста.\n\n"
            "Загляните в 🛍 Каталог, чтобы выбрать товары!",
            reply_markup=main_menu_kb(user_id)
        )
        return
    
    lines = []
    total = 0.0
    
    for product_id, count in cart_items:
        product = await get_product(product_id)
        if product:
            name, price = product[1], product[3]
            subtotal = price * count
            total += subtotal
            lines.append(f"• {name} — {price:.2f} ₽ × {count} = {subtotal:.2f} ₽")
    
    text = "🛒 <b>Ваша корзина:</b>\n\n" + "\n".join(lines)
    text += f"\n\n💰 <b>Итого: {total:.2f} ₽</b>"
    
    await message.answer(
        text,
        reply_markup=cart_kb()
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart_handler(callback: CallbackQuery) -> None:
    """Очистить корзину"""
    await callback.answer()
    
    user_id = callback.from_user.id
    await clear_cart(user_id)
    
    await callback.message.edit_text(
        "🗑 Корзина очищена!\n\n"
        "Загляните в 🛍 Каталог, чтобы выбрать товары!",
        reply_markup=main_menu_kb(user_id)
    )


@router.callback_query(F.data == 'checkout')
async def checkout_handler(callback: CallbackQuery) -> None:
    """Оформить заказ (заглушка)"""
    await callback.answer()
    
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Добавьте товары из каталога.",
            reply_markup=main_menu_kb(user_id)
        )
        return
    
    total = 0.0
    for product_id, count in cart_items:
        product = await get_product(product_id)
        if product:
            total += product[3] * count
    
    await callback.message.edit_text(
        f"💳 <b>Оформление заказа</b>\n\n"
        f"Сумма к оплате: <b>{total:.2f} ₽</b>\n\n"
        "🔜 Оплата временно недоступна.\n"
        "Свяжитесь с поддержкой для оплаты.",
        reply_markup=cart_kb()
    )
