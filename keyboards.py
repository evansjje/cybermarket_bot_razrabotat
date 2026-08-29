from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict

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

def categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat['name'], callback_data=f'cat_{cat["id"]}')
    builder.button(text='⬅️ Назад', callback_data='back_to_main')
    builder.adjust(1)
    return builder.as_markup()

def products_keyboard(products: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(text=f'{prod["name"]} — {prod["price"]}₽', callback_data=f'prod_{prod["id"]}')
    builder.button(text='⬅️ Назад', callback_data='back_to_categories')
    builder.adjust(1)
    return builder.as_markup()

def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ В корзину', callback_data=f'add_{product_id}')
    builder.button(text='⬅️ Назад', callback_data='back_to_products')
    builder.adjust(1)
    return builder.as_markup()

def cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить корзину', callback_data='clear_cart')
    builder.button(text='✅ Оформить заказ', callback_data='checkout')
    builder.button(text='⬅️ Назад', callback_data='back_to_main')
    builder.adjust(1)
    return builder.as_markup()

def admin_products_keyboard(products: List[Dict]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки списка товаров для удаления"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(text=f'❌ {prod["name"]}', callback_data=f'del_{prod["id"]}')
    builder.button(text='⬅️ Назад', callback_data='back_to_admin')
    builder.adjust(1)
    return builder.as_markup()

def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены FSM"""
    builder = ReplyKeyboardBuilder()
    builder.button(text='❌ Отмена')
    return builder.as_markup(resize_keyboard=True)
