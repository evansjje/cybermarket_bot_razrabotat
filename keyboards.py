# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any
from config import settings


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [KeyboardButton(text='🛍 Каталог')],
        [KeyboardButton(text='🛒 Корзина')],
        [KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы')],
        [KeyboardButton(text='🆘 Поддержка')],
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
        [KeyboardButton(text='⬅️ Назад')],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def product_card(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    buttons = [
        [
            InlineKeyboardButton(text='➕ В корзину', callback_data=f'add_to_cart:{product_id}'),
            InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_catalog')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_product_actions(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки для товара"""
    buttons = [
        [
            InlineKeyboardButton(text='✏️ Цена', callback_data=f'edit_price:{product_id}'),
            InlineKeyboardButton(text='📝 Описание', callback_data=f'edit_desc:{product_id}'),
            InlineKeyboardButton(text='🗑 Удалить', callback_data=f'delete_product:{product_id}')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_actions() -> InlineKeyboardMarkup:
    """Кнопки корзины"""
    buttons = [
        [
            InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart'),
            InlineKeyboardButton(text='💳 Оплатить', callback_data='checkout')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура категорий"""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat.get('title', 'Категория'),
            callback_data=f'category:{cat.get("id")}'
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура товаров в категории"""
    buttons = []
    for prod in products:
        buttons.append([InlineKeyboardButton(
            text=f"{prod.get('title', 'Товар')} — {prod.get('price', 0)}₽",
            callback_data=f'product:{prod.get("id")}'
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_categories')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
