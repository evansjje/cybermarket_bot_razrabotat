# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import settings


def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if user_id in settings.ADMIN_IDS:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def admin_menu_kb() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Добавить товар'))
    builder.row(KeyboardButton(text='📦 Список товаров'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)


def product_card_kb(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='➕ В корзину', callback_data=f'add_to_cart:{product_id}')
    )
    builder.row(
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_catalog')
    )
    return builder.as_markup()


def cart_kb() -> InlineKeyboardMarkup:
    """Кнопки корзины"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='💳 Оплатить', callback_data='checkout'),
        InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart')
    )
    builder.row(
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')
    )
    return builder.as_markup()


def back_to_main_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')
    )
    return builder.as_markup()


def back_to_catalog_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата к каталогу"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_catalog')
    )
    return builder.as_markup()
