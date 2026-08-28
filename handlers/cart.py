from aiogram import Router, types, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import main_menu

router = Router()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, db: Database) -> None:
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Перейдите в каталог и добавьте товары.",
            reply_markup=main_menu()
        )
        return
    
    # Формируем текст корзины
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        product = await db.get_product(item['product_id'])
        if product:
            item_total = product['price'] * item['count']
            total_price += item_total
            cart_text += (
                f"📦 <b>{product['name']}</b>\n"
                f"💰 {product['price']}₽ × {item['count']} = {item_total}₽\n\n"
            )
    
    cart_text += f"<b>Итого: {total_price}₽</b>"
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.button(text="🧹 Очистить корзину", callback_data="clear_cart")
    builder.button(text="✅ Оформить заказ", callback_data="checkout")
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    builder.adjust(1)
    
    await message.answer(
        cart_text,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, db: Database) -> None:
    """Очистить корзину"""
    await callback.answer()
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "🗑 Корзина очищена!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛍 Перейти в каталог", callback_data="catalog")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
                ]
            )
        )
    except Exception:
        pass


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, db: Database) -> None:
    """Оформление заказа"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "❌ Ваша корзина пуста!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🛍 Перейти в каталог", callback_data="catalog")],
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
                    ]
                )
            )
        except Exception:
            pass
        return
    
    # Создаем заказ
    total_price = 0
    order_items = []
    
    for item in cart_items:
        product = await db.get_product(item['product_id'])
        if product:
            item_total = product['price'] * item['count']
            total_price += item_total
            order_items.append(f"{product['name']} × {item['count']} = {item_total}₽")
    
    # Сохраняем заказ в БД
    await db.create_order(
        user_id=user_id,
        items="\n".join(order_items),
        total_price=total_price
    )
    
    # Очищаем корзину после заказа
    await db.clear_cart(user_id)
    
    order_text = (
        "✅ <b>Заказ оформлен!</b>\n\n"
        f"📋 <b>Состав заказа:</b>\n"
        f"{chr(10).join(order_items)}\n\n"
        f"💰 <b>Итого: {total_price}₽</b>\n\n"
        "⏳ Ожидайте, администратор свяжется с вами для оплаты и получения товара."
    )
    
    try:
        await callback.message.edit_text(
            order_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
                ]
            )
        )
    except Exception:
        pass


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    """Вернуться в главное меню"""
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )
