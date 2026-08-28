# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from keyboards import CartCallback, get_main_menu
from config import settings

router = Router()

@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database):
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста.\n\n"
            "Добавьте товары из каталога!",
            reply_markup=get_main_menu(user_id)
        )
        return
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_sum = 0
    
    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_sum = price * count
        total_sum += item_sum
        
        cart_text += f"📦 <b>{title}</b>\n"
        cart_text += f"💰 Цена: {price:.2f} ₽ × {count} шт.\n"
        cart_text += f"💵 Сумма: {item_sum:.2f} ₽\n"
        cart_text += "➖➖➖➖➖➖➖\n"
    
    cart_text += f"\n<b>Итого: {total_sum:.2f} ₽</b>"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    callback_data=CartCallback(action='pay').pack()
                ),
                InlineKeyboardButton(
                    text="🗑 Очистить",
                    callback_data=CartCallback(action='clear').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛍 Продолжить покупки",
                    callback_data=CartCallback(action='continue').pack()
                )
            ]
        ]
    )
    
    await message.answer(
        cart_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@router.callback_query(CartCallback.filter(F.action == 'clear'))
async def clear_cart(callback: CallbackQuery, db: Database):
    await callback.answer()
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "🗑 Корзина очищена!\n\n"
            "Добавьте новые товары из каталога.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🛍 Перейти в каталог",
                            callback_data=CartCallback(action='continue').pack()
                        )
                    ]
                ]
            )
        )
    except Exception:
        pass

@router.callback_query(CartCallback.filter(F.action == 'pay'))
async def pay_cart(callback: CallbackQuery, db: Database):
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "❌ Ваша корзина пуста!\n\n"
                "Добавьте товары перед оплатой.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🛍 Перейти в каталог",
                                callback_data=CartCallback(action='continue').pack()
                            )
                        ]
                    ]
                )
            )
        except Exception:
            pass
        return
    
    total_sum = sum(
        item.get('price', 0) * item.get('count', 1) 
        for item in cart_items
    )
    
    # Здесь должна быть интеграция с платёжной системой
    # Для примера просто показываем информацию
    payment_text = (
        f"💳 <b>Оплата заказа</b>\n\n"
        f"Сумма к оплате: <b>{total_sum:.2f} ₽</b>\n\n"
        f"🔒 Оплата через защищённое соединение.\n"
        f"📧 После оплаты товары будут отправлены вам в личные сообщения."
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить оплату",
                    callback_data=CartCallback(action='confirm_pay').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=CartCallback(action='cancel_pay').pack()
                )
            ]
        ]
    )
    
    try:
        await callback.message.edit_text(
            payment_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception:
        pass

@router.callback_query(CartCallback.filter(F.action == 'confirm_pay'))
async def confirm_payment(callback: CallbackQuery, db: Database):
    await callback.answer()
    user_id = callback.from_user.id
    
    # Здесь должна быть реальная обработка платежа
    # Для примера просто очищаем корзину и показываем сообщение
    
    cart_items = await db.get_cart(user_id)
    total_sum = sum(
        item.get('price', 0) * item.get('count', 1) 
        for item in cart_items
    )
    
    await db.clear_cart(user_id)
    
    success_text = (
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"💵 Сумма: {total_sum:.2f} ₽\n"
        f"🎁 Товары будут отправлены вам в ближайшее время.\n\n"
        f"Спасибо за покупку!"
    )
    
    try:
        await callback.message.edit_text(
            success_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🛍 Продолжить покупки",
                            callback_data=CartCallback(action='continue').pack()
                        )
                    ]
                ]
            ),
            parse_mode='HTML'
        )
    except Exception:
        pass

@router.callback_query(CartCallback.filter(F.action == 'cancel_pay'))
async def cancel_payment(callback: CallbackQuery, db: Database):
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "🛒 Ваша корзина пуста.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🛍 Перейти в каталог",
                                callback_data=CartCallback(action='continue').pack()
                            )
                        ]
                    ]
                )
            )
        except Exception:
            pass
        return
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_sum = 0
    
    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_sum = price * count
        total_sum += item_sum
        
        cart_text += f"📦 <b>{title}</b>\n"
        cart_text += f"💰 Цена: {price:.2f} ₽ × {count} шт.\n"
        cart_text += f"💵 Сумма: {item_sum:.2f} ₽\n"
        cart_text += "➖➖➖➖➖➖➖\n"
    
    cart_text += f"\n<b>Итого: {total_sum:.2f} ₽</b>"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    callback_data=CartCallback(action='pay').pack()
                ),
                InlineKeyboardButton(
                    text="🗑 Очистить",
                    callback_data=CartCallback(action='clear').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛍 Продолжить покупки",
                    callback_data=CartCallback(action='continue').pack()
                )
            ]
        ]
    )
    
    try:
        await callback.message.edit_text(
            cart_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception:
        pass

@router.callback_query(CartCallback.filter(F.action == 'continue'))
async def continue_shopping(callback: CallbackQuery, db: Database):
    await callback.answer()
    user_id = callback.from_user.id
    categories = await db.get_categories()
    
    from keyboards import get_categories_keyboard
    
    try:
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=get_categories_keyboard(categories, user_id)
        )
    except Exception:
        pass
