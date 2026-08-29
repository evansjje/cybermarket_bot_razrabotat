from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import main_menu

router = Router()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, state: FSMContext, db: Database):
    """Показать корзину пользователя"""
    await state.clear()
    
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста.\n\n"
            "Загляните в каталог, чтобы выбрать товары!",
            reply_markup=main_menu(user_id in settings.ADMIN_IDS)
        )
        return
    
    # Формируем текст корзины
    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    total = 0
    
    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_total = price * count
        total += item_total
        
        lines.append(
            f"📦 <b>{title}</b>\n"
            f"💰 {price:.2f} ₽ × {count} шт. = {item_total:.2f} ₽"
        )
        lines.append("")
    
    lines.append(f"<b>Итого: {total:.2f} ₽</b>")
    
    await message.answer(
        "\n".join(lines),
        reply_markup=cart_keyboard()
    )


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистить корзину"""
    await callback.answer()
    
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            "🗑 Корзина очищена!\n\n"
            "Загляните в каталог, чтобы выбрать новые товары.",
            reply_markup=None
        )
    except Exception:
        pass


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, db: Database):
    """Оформление заказа"""
    await callback.answer()
    
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        try:
            await callback.message.edit_text(
                "🛒 Ваша корзина пуста!",
                reply_markup=None
            )
        except Exception:
            pass
        return
    
    total = sum(
        item.get('price', 0) * item.get('count', 1)
        for item in cart_items
    )
    
    # Здесь можно добавить логику оплаты
    await db.clear_cart(user_id)
    
    try:
        await callback.message.edit_text(
            f"✅ <b>Заказ оформлен!</b>\n\n"
            f"💰 Сумма к оплате: {total:.2f} ₽\n\n"
            f"📩 В ближайшее время с вами свяжется администратор "
            f"для подтверждения оплаты и отправки товара.",
            reply_markup=None
        )
    except Exception:
        pass


def cart_keyboard():
    """Клавиатура для корзины"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Очистить", callback_data="clear_cart")
    builder.button(text="💳 Оплатить", callback_data="checkout")
    builder.adjust(2)
    return builder.as_markup()
