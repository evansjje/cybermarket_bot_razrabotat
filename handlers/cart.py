from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import main_menu

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Перейдите в каталог и добавьте товары.",
            reply_markup=main_menu(user_id in __import__('config').settings.ADMIN_IDS)
        )
        return
    
    total_price = 0
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    for item in cart_items:
        product = await db.get_product(item['product_id'])
        if product:
            item_total = product['price'] * item['count']
            total_price += item_total
            cart_text += (
                f"📦 <b>{product['name']}</b>\n"
                f"💰 Цена: {product['price']} ₽ × {item['count']} = {item_total} ₽\n\n"
            )
    
    cart_text += f"<b>Итого: {total_price} ₽</b>"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart'),
        InlineKeyboardButton(text='✅ Оформить заказ', callback_data='checkout')
    )
    keyboard.row(InlineKeyboardButton(text='⬅️ Назад в каталог', callback_data='catalog'))
    
    await message.answer(
        cart_text,
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистить корзину"""
    await callback.answer()
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "🗑 Корзина очищена!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='🛍 В каталог', callback_data='catalog')]]
            )
        )
    except Exception:
        pass


@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery, db: Database):
    """Оформление заказа"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.answer("❌ Корзина пуста!", show_alert=True)
        return
    
    total_price = 0
    order_details = []
    
    for item in cart_items:
        product = await db.get_product(item['product_id'])
        if product:
            item_total = product['price'] * item['count']
            total_price += item_total
            order_details.append(f"{product['name']} × {item['count']} = {item_total} ₽")
    
    # Создаем заказ
    order_id = await db.create_order(user_id, total_price)
    
    # Очищаем корзину после заказа
    await db.clear_cart(user_id)
    
    order_text = (
        f"✅ <b>Заказ #{order_id} оформлен!</b>\n\n"
        f"📦 Состав заказа:\n" + "\n".join(order_details) + f"\n\n"
        f"💰 Итого: {total_price} ₽\n\n"
        f"⏳ Ожидайте, администратор свяжется с вами для выдачи товара."
    )
    
    try:
        await callback.message.edit_text(
            order_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='🛍 Продолжить покупки', callback_data='catalog')]]
            )
        )
    except Exception:
        pass
