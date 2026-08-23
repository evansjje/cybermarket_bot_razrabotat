from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import get_connection
from keyboards import get_cart_keyboard, get_cart_actions_keyboard

router = Router()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message) -> None:
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """SELECT p.id, p.title, p.price, c.count 
               FROM cart c 
               JOIN products p ON c.product_id = p.id 
               WHERE c.user_id = ? 
               ORDER BY p.id""",
            (user_id,)
        )
        cart_items = await cursor.fetchall()
    finally:
        await conn.close()

    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста")
        return

    total_sum = sum(item["price"] * item["count"] for item in cart_items)
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        cart_text += (
            f"📦 <b>{item['title']}</b>\n"
            f"💰 Цена: {item['price']}₽\n"
            f"🔢 Количество: {item['count']}\n"
            f"💵 Сумма: {item['price'] * item['count']}₽\n\n"
        )
    cart_text += f"<b>Итого: {total_sum}₽</b>"

    keyboard = await get_cart_keyboard(cart_items)
    await message.answer(cart_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("cart_inc_"))
async def increase_cart_item(callback: CallbackQuery) -> None:
    """Увеличить количество товара в корзине"""
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[2])
    
    conn = await get_connection()
    try:
        await conn.execute(
            """UPDATE cart SET count = count + 1 
               WHERE user_id = ? AND product_id = ?""",
            (user_id, product_id)
        )
        await conn.commit()
    finally:
        await conn.close()
    
    await update_cart_message(callback)


@router.callback_query(F.data.startswith("cart_dec_"))
async def decrease_cart_item(callback: CallbackQuery) -> None:
    """Уменьшить количество товара в корзине"""
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[2])
    
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT count FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        item = await cursor.fetchone()
        
        if item and item["count"] > 1:
            await conn.execute(
                """UPDATE cart SET count = count - 1 
                   WHERE user_id = ? AND product_id = ?""",
                (user_id, product_id)
            )
        else:
            await conn.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
        await conn.commit()
    finally:
        await conn.close()
    
    await update_cart_message(callback)


@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery) -> None:
    """Очистить корзину"""
    user_id = callback.from_user.id
    
    conn = await get_connection()
    try:
        await conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await conn.commit()
    finally:
        await conn.close()
    
    await callback.message.edit_text("🗑 Корзина очищена")
    await callback.answer()


@router.callback_query(F.data == "cart_checkout")
async def checkout_cart(callback: CallbackQuery) -> None:
    """Оформить заказ"""
    user_id = callback.from_user.id
    
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """SELECT p.id, p.title, p.price, p.file_data, c.count 
               FROM cart c 
               JOIN products p ON c.product_id = p.id 
               WHERE c.user_id = ?""",
            (user_id,)
        )
        cart_items = await cursor.fetchall()
        
        if not cart_items:
            await callback.answer("🛒 Корзина пуста", show_alert=True)
            return
        
        total_sum = sum(item["price"] * item["count"] for item in cart_items)
        
        # Создание заказа
        cursor = await conn.execute(
            """INSERT INTO orders (user_id, total_amount, status) 
               VALUES (?, ?, 'paid')""",
            (user_id, total_sum)
        )
        order_id = cursor.lastrowid
        
        # Очистка корзины после заказа
        await conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await conn.commit()
    finally:
        await conn.close()
    
    # Формирование сообщения с товарами
    order_text = f"✅ <b>Заказ #{order_id} оплачен!</b>\n\n"
    for item in cart_items:
        order_text += f"📦 {item['title']} x{item['count']} — {item['price'] * item['count']}₽\n"
    order_text += f"\n💰 <b>Итого: {total_sum}₽</b>\n\n"
    order_text += "🎁 Ваши товары:\n\n"
    
    for item in cart_items:
        if item["file_data"]:
            order_text += f"📎 {item['title']}: {item['file_data']}\n"
        else:
            order_text += f"📎 {item['title']}: файл будет отправлен в личные сообщения\n"
    
    await callback.message.edit_text(order_text)
    await callback.answer("✅ Заказ успешно оплачен!", show_alert=True)


async def update_cart_message(callback: CallbackQuery) -> None:
    """Обновить сообщение корзины"""
    user_id = callback.from_user.id
    
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """SELECT p.id, p.title, p.price, c.count 
               FROM cart c 
               JOIN products p ON c.product_id = p.id 
               WHERE c.user_id = ? 
               ORDER BY p.id""",
            (user_id,)
        )
        cart_items = await cursor.fetchall()
    finally:
        await conn.close()

    if not cart_items:
        await callback.message.edit_text("🛒 Ваша корзина пуста")
        await callback.answer()
        return

    total_sum = sum(item["price"] * item["count"] for item in cart_items)
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        cart_text += (
            f"📦 <b>{item['title']}</b>\n"
            f"💰 Цена: {item['price']}₽\n"
            f"🔢 Количество: {item['count']}\n"
            f"💵 Сумма: {item['price'] * item['count']}₽\n\n"
        )
    cart_text += f"<b>Итого: {total_sum}₽</b>"

    keyboard = await get_cart_keyboard(cart_items)
    await callback.message.edit_text(cart_text, reply_markup=keyboard)
    await callback.answer()
