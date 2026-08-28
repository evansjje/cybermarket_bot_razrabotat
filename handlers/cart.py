from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_cart, clear_cart
from keyboards import main_menu_kb
from config import settings

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message):
    """Показ корзины пользователя"""
    user_id = message.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Перейдите в каталог и добавьте товары.",
            reply_markup=main_menu_kb(is_admin=user_id in settings.ADMIN_IDS)
        )
        return
    
    # Формируем текст корзины
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_sum = 0
    
    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_sum = price * count
        total_sum += item_sum
        
        cart_text += (
            f"📦 <b>{title}</b>\n"
            f"💰 Цена: {price}₽ | Количество: {count}\n"
            f"💵 Сумма: {item_sum}₽\n\n"
        )
    
    cart_text += f"━━━━━━━━━━━━━━━\n"
    cart_text += f"<b>Итого: {total_sum}₽</b>"
    
    # Кнопки для корзины
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart'),
        InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')
    )
    kb.row(InlineKeyboardButton(text='⬅️ В меню', callback_data='back_to_menu'))
    
    await message.answer(cart_text, reply_markup=kb.as_markup())


@router.callback_query(F.data == 'clear_cart')
async def clear_cart_handler(callback: CallbackQuery):
    """Очистка корзины"""
    await callback.answer("🗑 Корзина очищена!")
    user_id = callback.from_user.id
    await clear_cart(user_id)
    
    await callback.message.edit_text(
        "🛒 Ваша корзина пуста!\n\n"
        "Перейдите в каталог и добавьте товары.",
        reply_markup=main_menu_kb(is_admin=user_id in settings.ADMIN_IDS)
    )


@router.callback_query(F.data == 'pay_cart')
async def pay_cart_handler(callback: CallbackQuery):
    """Оплата корзины"""
    await callback.answer("💳 Оплата...")
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "❌ Ваша корзина пуста!",
            reply_markup=main_menu_kb(is_admin=user_id in settings.ADMIN_IDS)
        )
        return
    
    total_sum = sum(item.get('price', 0) * item.get('count', 1) for item in cart_items)
    
    # Здесь должна быть интеграция с платёжной системой
    # В демо-версии просто показываем информацию
    await callback.message.edit_text(
        f"💳 <b>Оплата заказа</b>\n\n"
        f"Сумма к оплате: <b>{total_sum}₽</b>\n\n"
        f"🔒 Оплата в разработке.\n"
        f"Свяжитесь с поддержкой для оплаты.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text='⬅️ В меню', callback_data='back_to_menu')
            ]]
        )
    )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    await callback.message.delete()
