from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database

router = Router()
db = Database()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return
    
    total_sum = 0
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    for item in cart_items:
        product = await db.get_product_by_id(item['product_id'])
        if product:
            item_total = product['price'] * item['count']
            total_sum += item_total
            text += (
                f"📦 <b>{product['name']}</b>\n"
                f"💰 {product['price']} ₽ x {item['count']} = {item_total} ₽\n\n"
            )
    
    text += f"<b>Итого: {total_sum} ₽</b>"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Оформить заказ', callback_data='checkout')],
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')]
    ])
    
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    await callback.answer()
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text("🗑 Корзина очищена!")
    except Exception:
        pass


@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery):
    """Оформить заказ"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.answer("❌ Корзина пуста!", show_alert=True)
        return
    
    total_sum = 0
    for item in cart_items:
        product = await db.get_product_by_id(item['product_id'])
        if product:
            total_sum += product['price'] * item['count']
    
    # Создаем заказ
    await db.db.execute(
        """INSERT INTO orders (user_id, total_amount, status) 
           VALUES (?, ?, 'pending')""",
        (user_id, total_sum)
    )
    await db.db.commit()
    
    # Очищаем корзину
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            f"✅ <b>Заказ оформлен!</b>\n\n"
            f"💰 Сумма: {total_sum} ₽\n"
            f"📋 Статус: В обработке\n\n"
            f"С вами свяжется администратор для уточнения деталей."
        )
    except Exception:
        pass
