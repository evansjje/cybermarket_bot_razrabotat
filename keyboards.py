# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


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


def categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    keyboard = []
    for cat in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=cat.get('title', 'Без названия'),
                callback_data=f"cat_{cat.get('id', 0)}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    keyboard = []
    for prod in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prod.get('title', 'Без названия')} — {prod.get('price', 0)}₽",
                callback_data=f"prod_{prod.get('id', 0)}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_categories')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    keyboard = [
        [InlineKeyboardButton(text='➕ В корзину', callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки для товаров"""
    keyboard = []
    for prod in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"✏️ {prod.get('title', 'Без названия')}",
                callback_data=f"admin_edit_{prod.get('id', 0)}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий с товаром в админке"""
    keyboard = [
        [
            InlineKeyboardButton(text='✏️ Цена', callback_data=f"price_{product_id}"),
            InlineKeyboardButton(text='📝 Описание', callback_data=f"desc_{product_id}")
        ],
        [InlineKeyboardButton(text='🗑 Удалить', callback_data=f"delete_{product_id}")],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_products')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def cart_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки корзины"""
    keyboard = [
        [
            InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart'),
            InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')
        ],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    keyboard = [
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
