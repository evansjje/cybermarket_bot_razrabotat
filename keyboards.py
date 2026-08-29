from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict, Any
from config import settings


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="🛒 Корзина"))
    builder.row(KeyboardButton(text="👥 Рефералка"), KeyboardButton(text="⭐ Отзывы"))
    builder.row(KeyboardButton(text="🆘 Поддержка"))
    if is_admin:
        builder.row(KeyboardButton(text="⚡ Админ-панель"))
    return builder.as_markup(resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📊 Статистика"), KeyboardButton(text="➕ Категория"))
    builder.row(KeyboardButton(text="➕ Товар"), KeyboardButton(text="📦 Товары"))
    builder.row(KeyboardButton(text="⬅️ Назад"))
    return builder.as_markup(resize_keyboard=True)


def categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat.get("title", "Категория"),
            callback_data=f"cat_{cat.get('id')}"
        )
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod.get('title', 'Товар')} — {prod.get('price', 0):.2f} ₽",
            callback_data=f"prod_{prod.get('id')}"
        )
    builder.adjust(1)
    return builder.as_markup()


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ В корзину", callback_data=f"buy_prod:{product_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки админки товара"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"📦 {prod.get('title', 'Товар')}",
            callback_data=f"admin_prod_{prod.get('id')}"
        )
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий над товаром в админке"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Цена", callback_data=f"edit_price:{product_id}")
    builder.button(text="📝 Описание", callback_data=f"edit_desc:{product_id}")
    builder.button(text="🗑 Удалить", callback_data=f"del_prod:{product_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_admin_products")
    builder.adjust(3, 1)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Очистить", callback_data="clear_cart")
    builder.button(text="💳 Оплатить", callback_data="pay_cart")
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    builder.adjust(2, 1)
    return builder.as_markup()


def back_to_categories_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад к категориям"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back_to_categories")
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад в меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    return builder.as_markup()


def product_admin_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для управления товаром в админке"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить", callback_data=f"edit_product:{product_id}")
    builder.button(text="🗑 Удалить", callback_data=f"delete_product:{product_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_admin_products")
    builder.adjust(2, 1)
    return builder.as_markup()


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Алиас для главного меню (совместимость)"""
    return main_menu(is_admin=is_admin)
