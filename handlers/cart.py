from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import main_menu
from config import settings

router = Router()


class PaymentStates(StatesGroup):
    waiting_for_payment = State()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message):
    """Показ корзины пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Перейдите в 🛍 Каталог, чтобы выбрать товары.",
            reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
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
        
        cart_text += f"📦 {title}\n"
        cart_text += f"💰 Цена: {price}₽ × {count} шт. = {item_sum}₽\n"
        cart_text += "➖➖➖➖➖➖➖\n"
    
    cart_text += f"\n<b>Итого: {total_sum}₽</b>"
    
    # Кнопки для корзины
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')],
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')],
        [InlineKeyboardButton(text='🛍 Продолжить покупки', callback_data='back_to_categories')]
    ])
    
    await message.answer(cart_text, reply_markup=keyboard)


@router.callback_query(F.data == 'clear_cart')
async def clear_cart_callback(callback: CallbackQuery):
    """Очистка корзины"""
    await callback.answer()
    
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "🗑 Корзина очищена!\n\n"
            "Перейдите в 🛍 Каталог, чтобы выбрать новые товары.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🛍 В каталог', callback_data='back_to_categories')]
            ])
        )
    except Exception:
        pass


@router.callback_query(F.data == 'pay_cart')
async def pay_cart_callback(callback: CallbackQuery, state: FSMContext):
    """Оплата корзины"""
    await callback.answer()
    
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "❌ Ваша корзина пуста!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='🛍 В каталог', callback_data='back_to_categories')]
                ])
            )
        except Exception:
            pass
        return
    
    total_sum = sum(item.get('price', 0) * item.get('count', 1) for item in cart_items)
    
    try:
        await callback.message.edit_text(
            f"💳 <b>Оплата заказа</b>\n\n"
            f"Сумма к оплате: <b>{total_sum}₽</b>\n\n"
            f"Для оплаты переведите указанную сумму на карту:\n"
            f"<code>1234 5678 9012 3456</code>\n\n"
            f"После оплаты нажмите кнопку ниже, чтобы подтвердить платеж.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='✅ Я оплатил(а)', callback_data='confirm_payment')],
                [InlineKeyboardButton(text='⬅️ Назад в корзину', callback_data='back_to_cart')]
            ])
        )
    except Exception:
        pass
    
    await state.set_state(PaymentStates.waiting_for_payment)


@router.callback_query(F.data == 'confirm_payment')
async def confirm_payment_callback(callback: CallbackQuery, state: FSMContext):
    """Подтверждение оплаты"""
    await callback.answer()
    
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "❌ Ваша корзина пуста!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='🛍 В каталог', callback_data='back_to_categories')]
                ])
            )
        except Exception:
            pass
        await state.clear()
        return
    
    total_sum = sum(item.get('price', 0) * item.get('count', 1) for item in cart_items)
    
    # Очищаем корзину после оплаты
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "✅ <b>Оплата подтверждена!</b>\n\n"
            f"Сумма: {total_sum}₽\n"
            "Ваш заказ будет обработан в ближайшее время.\n"
            "Спасибо за покупку! 🎉",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🛍 В каталог', callback_data='back_to_categories')]
            ])
        )
    except Exception:
        pass
    
    await state.clear()


@router.callback_query(F.data == 'back_to_cart')
async def back_to_cart_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в корзину"""
    await callback.answer()
    await state.clear()
    
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "🛒 Ваша корзина пуста!\n\n"
                "Перейдите в 🛍 Каталог, чтобы выбрать товары.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='🛍 В каталог', callback_data='back_to_categories')]
                ])
            )
        except Exception:
            pass
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
        
        cart_text += f"📦 {title}\n"
        cart_text += f"💰 Цена: {price}₽ × {count} шт. = {item_sum}₽\n"
        cart_text += "➖➖➖➖➖➖➖\n"
    
    cart_text += f"\n<b>Итого: {total_sum}₽</b>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')],
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')],
        [InlineKeyboardButton(text='🛍 Продолжить покупки', callback_data='back_to_categories')]
    ])
    
    try:
        await callback.message.edit_text(cart_text, reply_markup=keyboard)
    except Exception:
        pass


@router.message(F.text == '/cancel')
async def cancel_command(message: Message, state: FSMContext):
    """Отмена действия"""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu(is_admin=is_admin)
    )
