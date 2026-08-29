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
    for cat in categories:
        builder.button(
            text=cat.get('title', 'Без названия'),
            callback_data=f'cat_{cat.get("id", 0)}'
        )
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров в категории"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod.get('title', 'Без названия')} — {prod.get('price', 0)}₽",
            callback_data=f'prod_{prod.get("id", 0)}'
        )
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_categories'))
    builder.adjust(1)
    return builder.as_markup()


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='➕ В корзину', callback_data=f'buy_prod:{product_id}'),
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products')
    )
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


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров для админа"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"🆔 {prod.get('id', 0)} | {prod.get('title', 'Без названия')}",
            callback_data=f'adm_prod_{prod.get("id", 0)}'
        )
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin'))
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий над товаром для админа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✏️ Цена', callback_data=f'edit_price:{product_id}'),
        InlineKeyboardButton(text='📝 Описание', callback_data=f'edit_desc:{product_id}')
    )
    builder.row(
        InlineKeyboardButton(text='🗑 Удалить', callback_data=f'del_prod:{product_id}'),
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin_products')
    )
    return builder.as_markup()


def admin_categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий для админа (при добавлении товара)"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat.get('title', 'Без названия'),
            callback_data=f'adm_cat_{cat.get("id", 0)}'
        )
    builder.row(InlineKeyboardButton(text='⬅️ Отмена', callback_data='cancel_fsm'))
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены FSM"""
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data='cancel_fsm')
    return builder.as_markup()
