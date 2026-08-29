from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [KeyboardButton(text='🛍 Каталог')],
        [KeyboardButton(text='🛒 Корзина'), KeyboardButton(text='👥 Рефералка')],
        [KeyboardButton(text='⭐ Отзывы'), KeyboardButton(text='🆘 Поддержка')],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text='⚡ Админ-панель')])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню (алиас для main_menu_kb)"""
    return main_menu_kb(is_admin)


def admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    buttons = [
        [KeyboardButton(text='📊 Статистика')],
        [KeyboardButton(text='➕ Категория'), KeyboardButton(text='➕ Товар')],
        [KeyboardButton(text='📦 Товары')],
        [KeyboardButton(text='⬅️ Назад')],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat['title'],
            callback_data=f"cat_{cat['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    buttons = []
    for prod in products:
        buttons.append([InlineKeyboardButton(
            text=f"{prod['title']} — {prod['price']}₽",
            callback_data=f"prod_{prod['id']}"
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_categories')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    buttons = [
        [InlineKeyboardButton(text='➕ В корзину', callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки для списка товаров"""
    buttons = []
    for prod in products:
        buttons.append([InlineKeyboardButton(
            text=f"{prod['title']} — {prod['price']}₽",
            callback_data=f"admin_prod_{prod['id']}"
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий с товаром в админке"""
    buttons = [
        [
            InlineKeyboardButton(text='✏️ Цена', callback_data=f"edit_price_{product_id}"),
            InlineKeyboardButton(text='📝 Описание', callback_data=f"edit_desc_{product_id}")
        ],
        [InlineKeyboardButton(text='🗑 Удалить', callback_data=f"delete_{product_id}")],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back_to_products')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки корзины"""
    buttons = [
        [
            InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart'),
            InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')
        ],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='❌ Отмена')]],
        resize_keyboard=True
    )
