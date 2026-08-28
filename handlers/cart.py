# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database) -> None:
    """Показ корзины пользователя."""
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
        text += f"📦 {title}\n"
        text += f"💰 {price}₽ x {count} = {item_total}₽\n\n"

    text += f"<b>Итого: {total}₽</b>"

    # Клавиатура с кнопками очистки и оплаты
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    builder.button(text="💳 Оплатить", callback_data="pay_cart")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, db: Database) -> None:
    """Очистка корзины."""
    await callback.answer()
    user_id = callback.from_user.id
    await db.clear_cart(user_id)

    try:
        await callback.message.edit_text("🗑 Корзина очищена!")
    except Exception:
        pass


@router.callback_query(F.data == 'pay_cart')
async def pay_cart(callback: CallbackQuery, db: Database) -> None:
    """Оплата корзины."""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        try:
            await callback.message.edit_text("🛒 Ваша корзина пуста!")
        except Exception:
            pass
        return

    total = sum(item.get('price', 0) * item.get('count', 1) for item in cart_items)

    # Здесь можно добавить интеграцию с платёжной системой
    # В демо-версии просто показываем сообщение об оплате
    try:
        await callback.message.edit_text(
            f"💳 Оплата на сумму {total}₽\n\n"
            "🔗 Ссылка на оплату будет отправлена после настройки платёжной системы."
        )
    except Exception:
        pass
