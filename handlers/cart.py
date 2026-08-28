# handlers/cart.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from contextlib import suppress

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
            "Загляните в 🛍 Каталог, чтобы выбрать товары!",
            reply_markup=main_menu(is_admin=user_id in __import__('config').settings.ADMIN_IDS)
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
        lines.append(
            f"📦 <b>{title}</b>\n"
            f"   Цена: {price:.2f} ₽ | Кол-во: {count} | Сумма: {item_total:.2f} ₽"
        )
    
    lines.append(f"\n💰 <b>Итого: {total:.2f} ₽</b>")
    
    # Клавиатура с кнопками очистки и оплаты
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart'),
        InlineKeyboardButton(text='💳 Оплатить', callback_data='checkout')
    )
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    
    await message.answer(
        "\n".join(lines),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистить корзину"""
    await callback.answer()
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    with suppress(Exception):
        await callback.message.edit_text(
            "🗑 Корзина очищена!\n\n"
            "Загляните в 🛍 Каталог, чтобы выбрать товары!",
            reply_markup=main_menu(is_admin=user_id in __import__('config').settings.ADMIN_IDS)
        )


@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery, db: Database):
    """Оформление заказа"""
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        with suppress(Exception):
            await callback.message.edit_text(
                "🛒 Ваша корзина пуста!\n\n"
                "Загляните в 🛍 Каталог, чтобы выбрать товары!",
                reply_markup=main_menu(is_admin=user_id in __import__('config').settings.ADMIN_IDS)
            )
        return
    
    total = sum(item.get('price', 0) * item.get('count', 1) for item in cart_items)
    
    # Здесь можно добавить интеграцию с платёжной системой
    await db.clear_cart(user_id)
    
    with suppress(Exception):
        await callback.message.edit_text(
            f"✅ <b>Заказ оформлен!</b>\n\n"
            f"💰 Сумма к оплате: {total:.2f} ₽\n\n"
            f"📩 В ближайшее время с вами свяжется администратор для передачи товаров.\n"
            f"Спасибо за покупку!",
            reply_markup=main_menu(is_admin=user_id in __import__('config').settings.ADMIN_IDS)
        )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    
    with suppress(Exception):
        await callback.message.edit_text(
            "🏠 Главное меню\n\n"
            "Выберите раздел:",
            reply_markup=main_menu(is_admin=user_id in __import__('config').settings.ADMIN_IDS)
        )
