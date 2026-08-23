from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_cart_items, get_product, update_cart_item, remove_from_cart, clear_cart, get_cart_total
from keyboards import cart_keyboard, cart_actions_keyboard, main_menu_keyboard

router = Router()


class CartStates(StatesGroup):
    """Состояния для корзины"""
    viewing = State()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await get_cart_items(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста\n\n"
            "Перейдите в каталог и добавьте товары!",
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        product_id, title, price, count = item
        item_total = price * count
        total += item_total
        text += (
            f"📦 <b>{title}</b>\n"
            f"💰 {price} ₽ × {count} = {item_total} ₽\n"
            f"─────────────\n"
        )
    
    text += f"\n💎 <b>Итого: {total} ₽</b>"
    
    await message.answer(
        text,
        reply_markup=await cart_keyboard(cart_items),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cart_inc_"))
async def increase_count(callback: CallbackQuery):
    """Увеличить количество товара в корзине"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    await update_cart_item(user_id, product_id, 1)
    await refresh_cart(callback)
    await callback.answer()


@router.callback_query(F.data.startswith("cart_dec_"))
async def decrease_count(callback: CallbackQuery):
    """Уменьшить количество товара в корзине"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    await update_cart_item(user_id, product_id, -1)
    await refresh_cart(callback)
    await callback.answer()


@router.callback_query(F.data.startswith("cart_del_"))
async def delete_item(callback: CallbackQuery):
    """Удалить товар из корзины"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    await remove_from_cart(user_id, product_id)
    await refresh_cart(callback)
    await callback.answer("✅ Товар удален из корзины")


@router.callback_query(F.data == "cart_clear")
async def clear_cart_handler(callback: CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    await clear_cart(user_id)
    
    await callback.message.edit_text(
        "🗑 Корзина очищена\n\n"
        "Перейдите в каталог и добавьте новые товары!",
        reply_markup=main_menu_keyboard(user_id)
    )
    await callback.answer("✅ Корзина очищена")


@router.callback_query(F.data == "cart_pay")
async def pay_cart(callback: CallbackQuery):
    """Оплата корзины"""
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id)
    
    if not cart_items:
        await callback.answer("❌ Корзина пуста", show_alert=True)
        return
    
    total = await get_cart_total(user_id)
    
    await callback.message.edit_text(
        f"💳 <b>Оплата заказа</b>\n\n"
        f"Сумма к оплате: <b>{total} ₽</b>\n\n"
        f"Для оплаты переведите указанную сумму на карту:\n"
        f"<code>1234 5678 9012 3456</code>\n\n"
        f"После оплаты нажмите кнопку ниже и прикрепите чек.",
        reply_markup=await cart_actions_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cart_back")
async def back_to_cart(callback: CallbackQuery):
    """Вернуться к корзине"""
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста\n\n"
            "Перейдите в каталог и добавьте товары!",
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        product_id, title, price, count = item
        item_total = price * count
        total += item_total
        text += (
            f"📦 <b>{title}</b>\n"
            f"💰 {price} ₽ × {count} = {item_total} ₽\n"
            f"─────────────\n"
        )
    
    text += f"\n💎 <b>Итого: {total} ₽</b>"
    
    await callback.message.edit_text(
        text,
        reply_markup=await cart_keyboard(cart_items),
        parse_mode="HTML"
    )
    await callback.answer()


async def refresh_cart(callback: CallbackQuery):
    """Обновить отображение корзины"""
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста\n\n"
            "Перейдите в каталог и добавьте товары!",
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        product_id, title, price, count = item
        item_total = price * count
        total += item_total
        text += (
            f"📦 <b>{title}</b>\n"
            f"💰 {price} ₽ × {count} = {item_total} ₽\n"
            f"─────────────\n"
        )
    
    text += f"\n💎 <b>Итого: {total} ₽</b>"
    
    await callback.message.edit_text(
        text,
        reply_markup=await cart_keyboard(cart_items),
        parse_mode="HTML"
    )
