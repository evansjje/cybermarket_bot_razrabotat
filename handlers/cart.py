# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import (
    main_menu_kb,
    cart_kb,
    confirm_order_kb,
    back_to_menu_kb
)
from config import settings

router = Router()
db = Database()


class CartStates(StatesGroup):
    """Состояния для корзины."""
    viewing_cart = State()
    confirming_order = State()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, state: FSMContext):
    """Показать корзину пользователя."""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог, чтобы выбрать товары:",
            reply_markup=main_menu_kb(is_admin=user_id == settings.ADMIN_ID)
        )
        return
    
    # Формируем текст корзины
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        product = item.get("product", {})
        name = product.get("name", "Товар")
        price = product.get("price", 0)
        quantity = item.get("quantity", 1)
        item_total = price * quantity
        total_price += item_total
        
        cart_text += f"📦 <b>{name}</b>\n"
        cart_text += f"💰 Цена: {price}₽ × {quantity} = {item_total}₽\n"
        cart_text += f"🆔 ID: {item['id']}\n\n"
    
    cart_text += f"━━━━━━━━━━━━━━━\n"
    cart_text += f"<b>Итого: {total_price}₽</b>"
    
    await message.answer(
        cart_text,
        reply_markup=cart_kb(cart_items),
        parse_mode="HTML"
    )
    await state.set_state(CartStates.viewing_cart)


@router.callback_query(F.data.startswith("cart_remove_"))
async def remove_from_cart(callback: CallbackQuery, state: FSMContext):
    """Удалить товар из корзины."""
    cart_item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    await db.remove_from_cart(cart_item_id, user_id)
    
    # Показываем обновлённую корзину
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог, чтобы выбрать товары:",
            reply_markup=back_to_menu_kb()
        )
        await state.clear()
        return
    
    # Формируем текст корзины
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        product = item.get("product", {})
        name = product.get("name", "Товар")
        price = product.get("price", 0)
        quantity = item.get("quantity", 1)
        item_total = price * quantity
        total_price += item_total
        
        cart_text += f"📦 <b>{name}</b>\n"
        cart_text += f"💰 Цена: {price}₽ × {quantity} = {item_total}₽\n"
        cart_text += f"🆔 ID: {item['id']}\n\n"
    
    cart_text += f"━━━━━━━━━━━━━━━\n"
    cart_text += f"<b>Итого: {total_price}₽</b>"
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=cart_kb(cart_items),
        parse_mode="HTML"
    )
    await callback.answer("✅ Товар удалён из корзины")


@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery, state: FSMContext):
    """Очистить корзину."""
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    await callback.message.edit_text(
        "🗑 Корзина очищена!\n\n"
        "Загляните в каталог, чтобы выбрать товары:",
        reply_markup=back_to_menu_kb()
    )
    await state.clear()
    await callback.answer("✅ Корзина очищена")


@router.callback_query(F.data == "cart_checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    """Переход к оформлению заказа."""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог, чтобы выбрать товары:",
            reply_markup=back_to_menu_kb()
        )
        await state.clear()
        return
    
    # Формируем текст заказа
    order_text = "🧾 <b>Подтверждение заказа:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        product = item.get("product", {})
        name = product.get("name", "Товар")
        price = product.get("price", 0)
        quantity = item.get("quantity", 1)
        item_total = price * quantity
        total_price += item_total
        
        order_text += f"📦 <b>{name}</b> — {price}₽ × {quantity} = {item_total}₽\n"
    
    order_text += f"\n━━━━━━━━━━━━━━━\n"
    order_text += f"<b>Итого к оплате: {total_price}₽</b>\n\n"
    order_text += "Подтверждаете заказ?"
    
    await callback.message.edit_text(
        order_text,
        reply_markup=confirm_order_kb(),
        parse_mode="HTML"
    )
    await state.set_state(CartStates.confirming_order)


@router.callback_query(F.data == "order_confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение заказа."""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "❌ Ошибка: корзина пуста!",
            reply_markup=back_to_menu_kb()
        )
        await state.clear()
        return
    
    # Создаём заказ
    total_price = sum(
        item.get("product", {}).get("price", 0) * item.get("quantity", 1)
        for item in cart_items
    )
    
    order_id = await db.create_order(
        user_id=user_id,
        items=cart_items,
        total_price=total_price
    )
    
    # Очищаем корзину
    await db.clear_cart(user_id)
    
    # Формируем текст подтверждения
    order_text = (
        f"✅ <b>Заказ #{order_id} оформлен!</b>\n\n"
        f"💰 Сумма: {total_price}₽\n"
        f"📦 Товаров: {len(cart_items)}\n\n"
        f"⏳ Ожидайте подтверждения оплаты.\n"
        f"С вами свяжется администратор."
    )
    
    await callback.message.edit_text(
        order_text,
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer("✅ Заказ оформлен!")


@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена заказа."""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!",
            reply_markup=back_to_menu_kb()
        )
        await state.clear()
        return
    
    # Формируем текст корзины
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        product = item.get("product", {})
        name = product.get("name", "Товар")
        price = product.get("price", 0)
        quantity = item.get("quantity", 1)
        item_total = price * quantity
        total_price += item_total
        
        cart_text += f"📦 <b>{name}</b>\n"
        cart_text += f"💰 Цена: {price}₽ × {quantity} = {item_total}₽\n"
        cart_text += f"🆔 ID: {item['id']}\n\n"
    
    cart_text += f"━━━━━━━━━━━━━━━\n"
    cart_text += f"<b>Итого: {total_price}₽</b>"
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=cart_kb(cart_items),
        parse_mode="HTML"
    )
    await state.set_state(CartStates.viewing_cart)
    await callback.answer("❌ Заказ отменён")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    user_id = callback.from_user.id
    is_admin = (user_id == settings.ADMIN_ID)
    
    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    await state.clear()
