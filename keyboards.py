from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict, Any


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    return main_menu_kb(is_admin)


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
    for cat in categories:
        builder.button(
            text=cat.get('title', 'Без названия'),
            callback_data=f"cat_{cat.get('id', 0)}"
        )
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod.get('title', 'Без названия')} — {prod.get('price', 0)} ₽",
            callback_data=f"prod_{prod.get('id', 0)}"
        )
    builder.button(text='⬅️ Назад', callback_data='back_to_categories')
    builder.adjust(1)
    return builder.as_markup()


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ В корзину', callback_data=f"add_{product_id}")
    builder.button(text='⬅️ Назад', callback_data='back_to_products')
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    """Кнопки корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить', callback_data='clear_cart')
    builder.button(text='💳 Оплатить', callback_data='checkout')
    builder.button(text='⬅️ Назад', callback_data='back_to_menu')
    builder.adjust(2, 1)
    return builder.as_markup()


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки товара"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod.get('title', 'Без названия')}",
            callback_data=f"admin_prod_{prod.get('id', 0)}"
        )
    builder.button(text='⬅️ Назад', callback_data='admin_back')
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Кнопки управления товаром в админке"""
    builder = InlineKeyboardBuilder()
    builder.button(text='✏️ Цена', callback_data=f"edit_price_{product_id}")
    builder.button(text='📝 Описание', callback_data=f"edit_desc_{product_id}")
    builder.button(text='🗑 Удалить', callback_data=f"del_prod_{product_id}")
    builder.button(text='⬅️ Назад', callback_data='admin_products')
    builder.adjust(3, 1)
    return builder.as_markup()


def admin_categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура категорий для админки (выбор при добавлении товара)"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat.get('title', 'Без названия'),
            callback_data=f"admin_cat_{cat.get('id', 0)}"
        )
    builder.button(text='⬅️ Отмена', callback_data='admin_cancel')
    builder.adjust(1)
    return builder.as_markup()
