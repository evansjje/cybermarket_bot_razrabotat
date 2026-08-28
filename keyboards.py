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
        builder.button(
            text=category.get('title', 'Категория'),
            callback_data=f"cat_{category.get('id', 0)}"
        )
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров"""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product.get('title', 'Товар')} - {product.get('price', 0)}₽",
            callback_data=f"prod_{product.get('id', 0)}"
        )
    builder.adjust(1)
    return builder.as_markup()


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ В корзину', callback_data=f"add_{product_id}")
    builder.button(text='⬅️ Назад', callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки товара"""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product.get('title', 'Товар')}",
            callback_data=f"adm_prod_{product.get('id', 0)}"
        )
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий с товаром в админке"""
    builder = InlineKeyboardBuilder()
    builder.button(text='✏️ Цена', callback_data=f"price_{product_id}")
    builder.button(text='📝 Описание', callback_data=f"desc_{product_id}")
    builder.button(text='🗑 Удалить', callback_data=f"del_{product_id}")
    builder.adjust(3)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить корзину', callback_data="clear_cart")
    builder.button(text='💳 Оплатить', callback_data="pay")
    builder.button(text='⬅️ Назад', callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text='⬅️ Назад', callback_data="back_to_menu")
    return builder.as_markup()
