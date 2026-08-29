from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Database
from keyboards import main_menu

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста.\n\n"
            "Загляните в каталог, чтобы выбрать товары!",
            reply_markup=main_menu(is_admin=user_id in __import__('config').settings.ADMIN_IDS)
        )
        return

    # Формируем текст корзины
    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    total = 0

    for item in cart_items:
        title = item.get('title', 'Без названия')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_total = price * count
        total += item_total
        lines.append(f"• {title} — {price}₽ × {count} = {item_total}₽")

    lines.append(f"\n<b>Итого: {total}₽</b>")

    # Кнопки очистки и оплаты
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить корзину', callback_data='clear_cart')
    builder.button(text='💳 Оплатить', callback_data='checkout')
    builder.adjust(1)

    await message.answer(
        "\n".join(lines),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart_handler(callback: CallbackQuery, db: Database):
    """Очистить корзину"""
    await callback.answer()

    try:
        user_id = callback.from_user.id
        await db.clear_cart(user_id)

        await callback.message.edit_text(
            "🗑 Корзина очищена!",
            reply_markup=None
        )
    except Exception:
        pass


@router.callback_query(F.data == 'checkout')
async def checkout_handler(callback: CallbackQuery, db: Database):
    """Оформить заказ"""
    await callback.answer()

    try:
        user_id = callback.from_user.id
        cart_items = await db.get_cart(user_id)

        if not cart_items:
            await callback.message.edit_text(
                "❌ Корзина пуста!",
                reply_markup=None
            )
            return

        # Здесь можно добавить логику оплаты
        await db.clear_cart(user_id)

        await callback.message.edit_text(
            "✅ <b>Заказ оформлен!</b>\n\n"
            "Спасибо за покупку! Товары будут отправлены вам в ближайшее время.",
            reply_markup=None
        )
    except Exception:
        pass
