# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    buttons = [
        [KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина')],
        [KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы')],
        [KeyboardButton(text='🆘 Поддержка')]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text='⚡ Админ-панель')])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели."""
    buttons = [
        [KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Категория')],
        [KeyboardButton(text='➕ Товар'), KeyboardButton(text='📦 Товары')],
        [KeyboardButton(text='⬅️ Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора категории."""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat.get('title', 'Категория'),
            callback_data=f"cat_{cat.get('id', 0)}"
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора товара."""
    buttons = []
    for prod in products:
        buttons.append([InlineKeyboardButton(
            text=f"{prod.get('title', 'Товар')} - {prod.get('price', 0)}₽",
            callback_data=f"prod_{prod.get('id', 0)}"
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_categories')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура карточки товара."""
    buttons = [
        [InlineKeyboardButton(text='➕ В корзину', callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для админки со списком товаров."""
    buttons = []
    for prod in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{prod.get('title', 'Товар')}",
                callback_data=f"adm_prod_{prod.get('id', 0)}"
            )
        ])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура действий с товаром в админке."""
    buttons = [
        [
            InlineKeyboardButton(text='✏️ Цена', callback_data=f"edit_price_{product_id}"),
            InlineKeyboardButton(text='📝 Описание', callback_data=f"edit_desc_{product_id}")
        ],
        [InlineKeyboardButton(text='🗑 Удалить', callback_data=f"del_{product_id}")],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin_products')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура корзины."""
    buttons = [
        [InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='clear_cart')],
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='pay_cart')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    buttons = [[InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
