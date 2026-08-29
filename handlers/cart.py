# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import Database

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_total = price * count
        total += item_total
        
        text += (
            f"📦 {title}\n"
            f"💰 Цена: {price}₽ x {count} = {item_total}₽\n\n"
        )
    
    text += f"<b>Итого: {total}₽</b>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart"),
            InlineKeyboardButton(text="💳 Оплатить", callback_data="pay_cart")
        ],
        [
            InlineKeyboardButton(text="🛍 Продолжить покупки", callback_data="back_to_catalog")
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистить корзину"""
    await callback.answer()
    
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "🗑 Корзина очищена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍 В каталог", callback_data="back_to_catalog")]
            ])
        )
    except Exception:
        pass


@router.callback_query(F.data == 'pay_cart')
async def pay_cart(callback: CallbackQuery, db: Database):
    """Оплата корзины"""
    await callback.answer()
    
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text("🛒 Ваша корзина пуста!")
        except Exception:
            pass
        return
    
    total = sum(
        item.get('price', 0) * item.get('count', 1) 
        for item in cart_items
    )
    
    # Здесь должна быть интеграция с платёжной системой
    # В демо-версии просто очищаем корзину и показываем сообщение
    
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            f"✅ Оплата на сумму {total}₽ прошла успешно!\n\n"
            "🎉 Спасибо за покупку!\n"
            "Все товары будут отправлены вам в личные сообщения.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍 В каталог", callback_data="back_to_catalog")]
            ])
        )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_catalog')
async def back_to_catalog(callback: CallbackQuery, db: Database):
    """Вернуться в каталог"""
    await callback.answer()
    
    categories = await db.get_categories()
    
    from keyboards import categories_keyboard
    
    try:
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
    except Exception:
        pass
