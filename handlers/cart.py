from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import main_menu

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database) -> None:
    """Показывает содержимое корзины"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return
    
    total_price = 0
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    for item in cart_items:
        product = await db.get_product_by_id(item['product_id'])
        if not product:
            continue
        item_total = product['price'] * item['count']
        total_price += item_total
        text += (
            f"📦 <b>{product['name']}</b>\n"
            f"💰 Цена: {product['price']}₽\n"
            f"🔢 Количество: {item['count']}\n"
            f"📊 Итого: {item_total}₽\n\n"
        )
    
    text += f"<b>Общая сумма: {total_price}₽</b>"
    
    # Создаем инлайн-клавиатуру для корзины
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить корзину', callback_data='clear_cart')
    builder.button(text='✅ Оформить заказ', callback_data='checkout')
    builder.button(text='🛍 Продолжить покупки', callback_data='back_to_categories')
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, db: Database) -> None:
    """Очищает корзину пользователя"""
    await callback.answer()
    user_id = callback.from_user.id
    
    try:
        await db.clear_cart(user_id)
        await callback.message.edit_text(
            "🗑 Корзина очищена!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='🛍 В каталог', callback_data='back_to_categories')]]
            )
        )
    except Exception as e:
        await callback.message.edit_text("❌ Произошла ошибка при очистке корзины.")


@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery, db: Database) -> None:
    """Оформление заказа"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text("🛒 Ваша корзина пуста!")
        return
    
    total_price = 0
    order_details = []
    
    for item in cart_items:
        product = await db.get_product_by_id(item['product_id'])
        if not product:
            continue
        item_total = product['price'] * item['count']
        total_price += item_total
        order_details.append(f"{product['name']} x{item['count']} = {item_total}₽")
    
    # Создаем заказ в базе данных
    try:
        async with db.db.execute(
            """
            INSERT INTO orders (user_id, total_price, status)
            VALUES (?, ?, 'pending')
            """,
            (user_id, total_price)
        ) as cursor:
            order_id = cursor.lastrowid
        
        # Очищаем корзину после оформления заказа
        await db.clear_cart(user_id)
        await db.db.commit()
        
        order_text = (
            f"✅ <b>Заказ #{order_id} оформлен!</b>\n\n"
            f"📋 Состав заказа:\n"
            + "\n".join(order_details) +
            f"\n\n💰 <b>Итого: {total_price}₽</b>\n"
            f"⏳ Статус: Ожидает оплаты\n\n"
            f"📩 С вами свяжется администратор для уточнения деталей."
        )
        
        await callback.message.edit_text(
            order_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='🛍 Продолжить покупки', callback_data='back_to_categories')]]
            )
        )
    except Exception as e:
        await callback.message.edit_text("❌ Произошла ошибка при оформлении заказа.")


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery, db: Database) -> None:
    """Возвращает к списку категорий"""
    await callback.answer()
    categories = await db.get_categories()
    
    if not categories:
        await callback.message.edit_text("📭 Каталог пуст.")
        return
    
    from keyboards import categories_keyboard
    try:
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
    except Exception as e:
        pass
