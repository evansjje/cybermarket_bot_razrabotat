from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
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


def admin_menu_kb() -> ReplyKeyboardMarkup:
    """Меню админки"""
    buttons = [
        [KeyboardButton(text='📊 Статистика')],
        [KeyboardButton(text='➕ Категория'), KeyboardButton(text='➕ Товар')],
        [KeyboardButton(text='📦 Товары')],
        [KeyboardButton(text='⬅️ Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def categories_kb(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat.get('title', 'Категория'),
            callback_data=f'cat_{cat.get("id")}'
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_main')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_kb(products: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров"""
    buttons = []
    for prod in products:
        buttons.append([InlineKeyboardButton(
            text=f"{prod.get('title', 'Товар')} - {prod.get('price', 0)}₽",
            callback_data=f'prod_{prod.get("id")}'
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_cat')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_kb(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки товара"""
    buttons = [
        [InlineKeyboardButton(text='➕ В корзину', callback_data=f'buy_{product_id}')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_prod')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки детального просмотра товара"""
    buttons = [
        [InlineKeyboardButton(text='➕ В корзину', callback_data=f'buy_{product_id}')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_prod')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_products_kb(products: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки для товаров"""
    buttons = []
    for prod in products:
        prod_id = prod.get('id')
        buttons.append([
            InlineKeyboardButton(text=f"✏️ {prod.get('title', 'Товар')}", callback_data=f'edit_price_{prod_id}'),
            InlineKeyboardButton(text='📝', callback_data=f'edit_desc_{prod_id}'),
            InlineKeyboardButton(text='🗑', callback_data=f'del_prod_{prod_id}')
        ])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_admin')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки детального просмотра товара в админке"""
    buttons = [
        [InlineKeyboardButton(text='✏️ Изменить цену', callback_data=f'edit_price_{product_id}')],
        [InlineKeyboardButton(text='📝 Изменить описание', callback_data=f'edit_desc_{product_id}')],
        [InlineKeyboardButton(text='🗑 Удалить', callback_data=f'del_prod_{product_id}')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_admin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_kb() -> InlineKeyboardMarkup:
    """Кнопки корзины"""
    buttons = [
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='checkout')],
        [InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_kb() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_main')]
    ])
