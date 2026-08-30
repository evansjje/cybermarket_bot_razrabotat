# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards import cart_actions, main_menu
from config import settings

router = Router()
db = Database()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message):
    """Показ корзины пользователя"""
    user_id = message.from_user.id

    await db.connect()
    cart_items = await db.get_cart(user_id)
    await db.close()

    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста.\n\n"
            "Перейдите в каталог и добавьте товары!",
            reply_markup=main_menu(message.from_user.id in settings.ADMIN_IDS)
        )
        return

    # Формируем текст корзины
    lines = []
    total = 0
    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        subtotal = price * count
        total += subtotal
        lines.append(f"🛍 {title}\n💰 {price}₽ × {count} = {subtotal}₽")

    text = (
        "🛒 <b>Ваша корзина:</b>\n\n"
        + "\n\n".join(lines)
        + f"\n\n<b>Итого: {total}₽</b>"
    )

    await message.answer(
        text,
        reply_markup=cart_actions()
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery):
    """Очистка корзины"""
    await callback.answer("🗑 Корзина очищена!")

    user_id = callback.from_user.id

    await db.connect()
    await db.clear_cart(user_id)
    await db.close()

    try:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста.\n\n"
            "Перейдите в каталог и добавьте товары!",
            reply_markup=main_menu(callback.from_user.id in settings.ADMIN_IDS)
        )
    except Exception:
        pass


@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery):
    """Оформление заказа"""
    await callback.answer("💳 Оплата временно недоступна!")

    try:
        await callback.message.edit_text(
            "💳 <b>Оплата</b>\n\n"
            "К сожалению, оплата временно недоступна.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой.",
            reply_markup=main_menu(callback.from_user.id in settings.ADMIN_IDS)
        )
    except Exception:
        pass
