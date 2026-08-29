# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [KeyboardButton(text='🛍 Каталог')],
        [KeyboardButton(text='🛒 Корзина')],
        [KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы')],
        [KeyboardButton(text='🆘 Поддержка')]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text='⚡ Админ-панель')])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    buttons = [
        [KeyboardButton(text='📊 Статистика')],
        [KeyboardButton(text='➕ Категория'), KeyboardButton(text='➕ Товар')],
        [KeyboardButton(text='📦 Товары')],
        [KeyboardButton(text='⬅️ Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat['title'],
            callback_data=f"cat_{cat['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров в категории"""
    buttons = []
    for prod in products:
        buttons.append([InlineKeyboardButton(
            text=f"{prod['title']} - {prod['price']}₽",
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


def cart_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки корзины"""
    buttons = [
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')],
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_products_keyboard(products: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки для товаров"""
    buttons = []
    for prod in products:
        buttons.append([
            InlineKeyboardButton(text=f"✏️ {prod['title']}", callback_data=f"edit_price_{prod['id']}"),
            InlineKeyboardButton(text='📝', callback_data=f"edit_desc_{prod['id']}"),
            InlineKeyboardButton(text='🗑', callback_data=f"del_prod_{prod['id']}")
        ])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки для выбора категории при добавлении товара"""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat['title'],
            callback_data=f"admin_cat_{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Отмена', callback_data='cancel_fsm')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    buttons = [[InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
