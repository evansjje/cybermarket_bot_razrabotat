# handlers/cart.py
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery

from database import Database
from keyboards import (
    cart_kb,
    main_menu_kb,
    checkout_kb
)
from config import settings

router = Router()
db = Database()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог и выберите что-нибудь интересное:",
            reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
        )
        return
    
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        cart_text += (
            f"<b>{item['name']}</b>\n"
            f"💰 Цена: {item['price']}₽\n"
            f"📦 Количество: {item['quantity']}\n"
            f"─────────────\n"
        )
    
    cart_text += f"\n<b>Итого: {total_price}₽</b>"
    
    await message.answer(
        cart_text,
        reply_markup=cart_kb(cart_items)
    )


@router.callback_query(F.data.startswith("cart_remove_"))
async def remove_from_cart(callback: CallbackQuery):
    """Удалить товар из корзины"""
    cart_item_id = int(callback.data.split("_")[2])
    
    await db.remove_from_cart(cart_item_id)
    
    # Показываем обновленную корзину
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог и выберите что-нибудь интересное:",
            reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
        )
        await callback.answer("Товар удален из корзины")
        return
    
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        cart_text += (
            f"<b>{item['name']}</b>\n"
            f"💰 Цена: {item['price']}₽\n"
            f"📦 Количество: {item['quantity']}\n"
            f"─────────────\n"
        )
    
    cart_text += f"\n<b>Итого: {total_price}₽</b>"
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=cart_kb(cart_items)
    )
    await callback.answer("Товар удален из корзины")


@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    
    await db.clear_cart(user_id)
    
    await callback.message.edit_text(
        "🗑 Корзина очищена!\n\n"
        "Загляните в каталог и выберите что-нибудь интересное:",
        reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
    )
    await callback.answer("Корзина очищена")


@router.callback_query(F.data == "cart_checkout")
async def checkout(callback: CallbackQuery):
    """Переход к оформлению заказа"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог и выберите что-нибудь интересное:",
            reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
        )
        await callback.answer()
        return
    
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    
    checkout_text = (
        "🧾 <b>Оформление заказа</b>\n\n"
        f"Товаров в корзине: {len(cart_items)}\n"
        f"<b>Сумма к оплате: {total_price}₽</b>\n\n"
        "Для оплаты нажмите кнопку ниже. "
        "После оплаты товары будут отправлены вам в личные сообщения."
    )
    
    await callback.message.edit_text(
        checkout_text,
        reply_markup=checkout_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "checkout_confirm")
async def confirm_checkout(callback: CallbackQuery):
    """Подтверждение оплаты заказа"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог и выберите что-нибудь интересное:",
            reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
        )
        await callback.answer()
        return
    
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Создаем заказ
    order_id = await db.create_order(
        user_id=user_id,
        items=cart_items,
        total_price=total_price
    )
    
    # Очищаем корзину после создания заказа
    await db.clear_cart(user_id)
    
    # Формируем подтверждение
    order_text = (
        "✅ <b>Заказ успешно оформлен!</b>\n\n"
        f"📋 Номер заказа: <b>#{order_id}</b>\n"
        f"💰 Сумма: <b>{total_price}₽</b>\n\n"
        "🎁 Ваши товары:\n"
    )
    
    for item in cart_items:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    
    order_text += (
        "\n📩 Товары будут отправлены вам в ближайшее время.\n"
        "Спасибо за покупку!"
    )
    
    await callback.message.edit_text(
        order_text,
        reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
    )
    await callback.answer("Заказ оформлен!")


@router.callback_query(F.data == "checkout_cancel")
async def cancel_checkout(callback: CallbackQuery):
    """Отмена оформления заказа"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог и выберите что-нибудь интересное:",
            reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
        )
        await callback.answer()
        return
    
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        cart_text += (
            f"<b>{item['name']}</b>\n"
            f"💰 Цена: {item['price']}₽\n"
            f"📦 Количество: {item['quantity']}\n"
            f"─────────────\n"
        )
    
    cart_text += f"\n<b>Итого: {total_price}₽</b>"
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=cart_kb(cart_items)
    )
    await callback.answer("Оформление отменено")
