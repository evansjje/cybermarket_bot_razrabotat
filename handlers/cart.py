from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Database
from keyboards import main_menu

router = Router()
db = Database()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return
    
    total_sum = 0
    text = "🛒 Ваша корзина:\n\n"
    
    for item in cart_items:
        product = await db.get_product_by_id(item['product_id'])
        if product:
            item_total = product['price'] * item['count']
            total_sum += item_total
            text += f"📦 {product['name']}\n"
            text += f"💰 Цена: {product['price']} ₽ x {item['count']} = {item_total} ₽\n\n"
    
    text += f"💎 Итого: {total_sum} ₽"
    
    # Создаем инлайн-клавиатуру для корзины
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart'),
        InlineKeyboardButton(text='✅ Оформить заказ', callback_data='checkout')
    )
    
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text("🗑 Корзина очищена!")
    except Exception:
        pass


@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text("🛒 Ваша корзина пуста!")
        except Exception:
            pass
        return
    
    # Создаем заказ
    total_sum = 0
    for item in cart_items:
        product = await db.get_product_by_id(item['product_id'])
        if product:
            total_sum += product['price'] * item['count']
    
    # Сохраняем заказ в БД
    await db.db.execute(
        "INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, ?)",
        (user_id, total_sum, 'pending')
    )
    await db.db.commit()
    
    # Очищаем корзину после оформления
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            f"✅ Заказ оформлен!\n\n"
            f"💰 Сумма заказа: {total_sum} ₽\n"
            f"📋 Статус: Ожидает оплаты\n\n"
            f"С вами свяжется администратор для уточнения деталей."
        )
    except Exception:
        pass
