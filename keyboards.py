from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict, Any
from database import Database


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Категория'))
    builder.row(KeyboardButton(text='➕ Товар'), KeyboardButton(text='📦 Товары'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)


async def categories_keyboard(db: Database) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    categories = await db.get_categories()
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat['name'], callback_data=f'cat_{cat["id"]}')
    builder.adjust(2)
    return builder.as_markup()


async def products_keyboard(category_id: int, db: Database) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    products = await db.get_products_by_category(category_id)
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(text=prod['name'], callback_data=f'prod_{prod["id"]}')
    builder.button(text='⬅️ Назад', callback_data='back_to_categories')
    builder.adjust(1)
    return builder.as_markup()


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ В корзину', callback_data=f'add_{product_id}')
    builder.button(text='⬅️ Назад', callback_data='back_to_products')
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить корзину', callback_data='clear_cart')
    builder.button(text='✅ Оформить заказ', callback_data='checkout')
    builder.button(text='⬅️ Назад', callback_data='back_to_menu')
    builder.adjust(1)
    return builder.as_markup()


async def admin_products_keyboard(db: Database) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров для админа (с удалением)"""
    products = await db.get_all_products()
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(text=f'❌ {prod["name"]}', callback_data=f'delprod_{prod["id"]}')
    builder.button(text='⬅️ Назад', callback_data='back_to_admin')
    builder.adjust(1)
    return builder.as_markup()


def cancel_fsm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены FSM"""
    builder = ReplyKeyboardBuilder()
    builder.button(text='❌ Отмена')
    return builder.as_markup(resize_keyboard=True)
