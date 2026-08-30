# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import Database
from keyboards import main_menu

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message, db: Database):
    """Показ корзины пользователя."""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)

    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста!\n\n"
            "Загляните в каталог, чтобы выбрать товары.",
            reply_markup=main_menu()
        )
        return

    # Формируем текст корзины
    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    total = 0.0

    for item in cart_items:
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        count = item.get('count', 1)
        item_total = price * count
        total += item_total
        lines.append(f"• {title} — {price}₽ × {count} = {item_total}₽")

    lines.append(f"\n💰 <b>Итого: {total}₽</b>")

    # Клавиатура с действиями
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')],
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]
    ])

    await message.answer(
        "\n".join(lines),
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистка корзины."""
    await callback.answer()

    try:
        user_id = callback.from_user.id
        await db.clear_cart(user_id)

        await callback.message.edit_text(
            "🗑 Корзина очищена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]
            ])
        )
    except Exception:
        pass


@router.callback_query(F.data == 'pay_cart')
async def pay_cart(callback: CallbackQuery, db: Database):
    """Оплата корзины."""
    await callback.answer()

    try:
        user_id = callback.from_user.id
        cart_items = await db.get_cart(user_id)

        if not cart_items:
            await callback.message.edit_text(
                "❌ Корзина пуста!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]
                ])
            )
            return

        total = sum(
            item.get('price', 0) * item.get('count', 1)
            for item in cart_items
        )

        await callback.message.edit_text(
            f"💳 <b>Оплата заказа</b>\n\n"
            f"Сумма к оплате: <b>{total}₽</b>\n\n"
            f"🔗 Для оплаты перейдите по ссылке:\n"
            f"https://t.me/CyberMarket_PayBot\n\n"
            f"После оплаты нажмите кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='✅ Я оплатил', callback_data='confirm_payment')],
                [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]
            ]),
            parse_mode='HTML'
        )
    except Exception:
        pass


@router.callback_query(F.data == 'confirm_payment')
async def confirm_payment(callback: CallbackQuery, db: Database):
    """Подтверждение оплаты."""
    await callback.answer()

    try:
        user_id = callback.from_user.id
        cart_items = await db.get_cart(user_id)

        if not cart_items:
            await callback.message.edit_text(
                "❌ Корзина пуста!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]
                ])
            )
            return

        # Формируем текст с товарами
        items_text = []
        for item in cart_items:
            title = item.get('title', 'Товар')
            price = item.get('price', 0)
            count = item.get('count', 1)
            items_text.append(f"• {title} — {price}₽ × {count}")

        # Очищаем корзину после оплаты
        await db.clear_cart(user_id)

        await callback.message.edit_text(
            "✅ <b>Оплата подтверждена!</b>\n\n"
            "📦 Ваши товары:\n" + "\n".join(items_text) + "\n\n"
            "🔑 Коды и ключи будут отправлены вам в личные сообщения в течение 5 минут.\n\n"
            "Спасибо за покупку! 🎉",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='⬅️ В меню', callback_data='back_to_main')]
            ]),
            parse_mode='HTML'
        )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню."""
    await callback.answer()

    try:
        from config import settings
        is_admin = callback.from_user.id in settings.ADMIN_IDS

        await callback.message.delete()
        await callback.message.answer(
            "🏠 Главное меню",
            reply_markup=main_menu(is_admin)
        )
    except Exception:
        pass
