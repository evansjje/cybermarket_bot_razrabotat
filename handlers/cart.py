from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database import Database
from keyboards import main_menu
from config import settings

router = Router()


class PaymentStates(StatesGroup):
    waiting_for_payment = State()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database) -> None:
    """Показ корзины пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Перейдите в каталог и добавьте товары.",
            reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
        )
        return
    
    # Формируем текст корзины
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_sum = 0
    
    for item in cart_items:
        title = item.get('title', 'Без названия')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_sum = price * count
        total_sum += item_sum
        
        cart_text += (
            f"📦 <b>{title}</b>\n"
            f"💰 Цена: {price} ₽ × {count} шт. = <b>{item_sum} ₽</b>\n\n"
        )
    
    cart_text += f"━━━━━━━━━━━━━━━\n"
    cart_text += f"<b>Итого: {total_sum} ₽</b>"
    
    # Создаем клавиатуру с кнопками очистки и оплаты
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🗑 Очистить корзину",
            callback_data="clear_cart"
        ),
        InlineKeyboardButton(
            text="💳 Оплатить",
            callback_data="pay_cart"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data="back_to_menu"
        )
    )
    
    await message.answer(
        cart_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, db: Database) -> None:
    """Очистка корзины"""
    await callback.answer()
    user_id = callback.from_user.id
    
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "🗑 Корзина очищена!\n\n"
            "Перейдите в каталог, чтобы добавить новые товары.",
            reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
        )
    except Exception:
        pass


@router.callback_query(F.data == 'pay_cart')
async def pay_cart(callback: CallbackQuery, db: Database) -> None:
    """Оплата корзины"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "❌ Ваша корзина пуста!\n\n"
                "Добавьте товары перед оплатой.",
                reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
            )
        except Exception:
            pass
        return
    
    # Формируем текст заказа
    order_text = "🧾 <b>Ваш заказ:</b>\n\n"
    total_sum = 0
    
    for item in cart_items:
        title = item.get('title', 'Без названия')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_sum = price * count
        total_sum += item_sum
        
        order_text += (
            f"📦 <b>{title}</b>\n"
            f"💰 {price} ₽ × {count} шт. = <b>{item_sum} ₽</b>\n\n"
        )
    
    order_text += f"━━━━━━━━━━━━━━━\n"
    order_text += f"<b>Итого к оплате: {total_sum} ₽</b>\n\n"
    order_text += "💳 Для оплаты свяжитесь с поддержкой: @support"
    
    # Создаем клавиатуру для подтверждения
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data="confirm_order"
        ),
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="cancel_order"
        )
    )
    
    try:
        await callback.message.edit_text(
            order_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data == 'confirm_order')
async def confirm_order(callback: CallbackQuery, db: Database) -> None:
    """Подтверждение заказа"""
    await callback.answer()
    user_id = callback.from_user.id
    
    # Очищаем корзину после подтверждения
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "✅ <b>Заказ подтвержден!</b>\n\n"
            "🎉 Спасибо за покупку!\n"
            "Товары будут отправлены вам в ближайшее время.\n\n"
            "Если у вас возникли вопросы, обратитесь в поддержку.",
            reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
        )
    except Exception:
        pass


@router.callback_query(F.data == 'cancel_order')
async def cancel_order(callback: CallbackQuery, db: Database) -> None:
    """Отмена заказа"""
    await callback.answer()
    user_id = callback.from_user.id
    
    # Возвращаемся к корзине
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "🛒 Ваша корзина пуста!",
                reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
            )
        except Exception:
            pass
        return
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_sum = 0
    
    for item in cart_items:
        title = item.get('title', 'Без названия')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_sum = price * count
        total_sum += item_sum
        
        cart_text += (
            f"📦 <b>{title}</b>\n"
            f"💰 Цена: {price} ₽ × {count} шт. = <b>{item_sum} ₽</b>\n\n"
        )
    
    cart_text += f"━━━━━━━━━━━━━━━\n"
    cart_text += f"<b>Итого: {total_sum} ₽</b>"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🗑 Очистить корзину",
            callback_data="clear_cart"
        ),
        InlineKeyboardButton(
            text="💳 Оплатить",
            callback_data="pay_cart"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data="back_to_menu"
        )
    )
    
    try:
        await callback.message.edit_text(
            cart_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery, db: Database) -> None:
    """Возврат в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    
    try:
        await callback.message.edit_text(
            "🏠 Вы в главном меню.\n"
            "Выберите действие:",
            reply_markup=main_menu(is_admin=user_id in settings.ADMIN_IDS)
        )
    except Exception:
        pass
