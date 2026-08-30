# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict, Any


def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Категория'))
    builder.row(KeyboardButton(text='➕ Товар'), KeyboardButton(text='📦 Товары'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)


def get_categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура категорий для каталога"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(InlineKeyboardButton(
            text=cat.get('title', 'Категория'),
            callback_data=f"cat_{cat.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    return builder.as_markup()


def get_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура товаров в категории"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.row(InlineKeyboardButton(
            text=f"{prod.get('title', 'Товар')} — {prod.get('price', 0)}₽",
            callback_data=f"prod_{prod.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_categories'))
    return builder.as_markup()


def get_product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='➕ В корзину', callback_data=f"add_{product_id}"))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products'))
    return builder.as_markup()


def get_cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart'))
    builder.row(InlineKeyboardButton(text='💳 Оплатить', callback_data='pay'))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_menu'))
    return builder.as_markup()


def get_admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура списка товаров для админа"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.row(InlineKeyboardButton(
            text=f"{prod.get('title', 'Товар')}",
            callback_data=f"admin_prod_{prod.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back'))
    return builder.as_markup()


def get_admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий с товаром для админа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✏️ Цена', callback_data=f"edit_price_{product_id}"),
        InlineKeyboardButton(text='📝 Описание', callback_data=f"edit_desc_{product_id}")
    )
    builder.row(InlineKeyboardButton(text='🗑 Удалить', callback_data=f"delete_prod_{product_id}"))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_products'))
    return builder.as_markup()


def get_admin_categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура категорий для админа (при добавлении товара)"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(InlineKeyboardButton(
            text=cat.get('title', 'Категория'),
            callback_data=f"admin_cat_{cat.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back'))
    return builder.as_markup()
