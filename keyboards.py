# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict, Any


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню (алиас для main_menu)"""
    return main_menu(is_admin)


def admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Категория'))
    builder.row(KeyboardButton(text='➕ Товар'), KeyboardButton(text='📦 Товары'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)


def categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(
            text=category.get('title', 'Категория'),
            callback_data=f"cat_{category.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    return builder.as_markup()


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров в категории"""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f"{product.get('title')} — {product.get('price')}₽",
            callback_data=f"prod_{product.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_categories'))
    return builder.as_markup()


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='➕ В корзину', callback_data=f"add_{product_id}"))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products'))
    return builder.as_markup()


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров для админа"""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f"{product.get('title')} — {product.get('price')}₽",
            callback_data=f"admin_prod_{product.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin'))
    return builder.as_markup()


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий с товаром для админа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✏️ Цена', callback_data=f"edit_price_{product_id}"),
        InlineKeyboardButton(text='📝 Описание', callback_data=f"edit_desc_{product_id}")
    )
    builder.row(InlineKeyboardButton(text='🗑 Удалить', callback_data=f"delete_prod_{product_id}"))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin_products'))
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки корзины"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart'),
        InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')
    )
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    return builder.as_markup()
