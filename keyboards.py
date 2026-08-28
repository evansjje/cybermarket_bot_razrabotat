from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Optional, Any
from config import settings


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню (алиас для main_menu)"""
    return main_menu()


def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [KeyboardButton(text='🛍 Каталог')],
        [KeyboardButton(text='🛒 Корзина')],
        [KeyboardButton(text='👥 Рефералка')],
        [KeyboardButton(text='⭐ Отзывы')],
        [KeyboardButton(text='🆘 Поддержка')],
    ]
    
    # Добавляем кнопку админ-панели для админов
    if settings.ADMIN_IDS:
        buttons.append([KeyboardButton(text='⚡ Админ-панель')])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True
    )


def categories_menu(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки категорий"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.button(
            text=category['name'],
            callback_data=f"category_{category['id']}"
        )
    
    builder.button(text='⬅️ Назад', callback_data='back_to_menu')
    builder.adjust(1)
    
    return builder.as_markup()


def products_menu(products: List[Dict[str, Any]], category_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки товаров категории"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        builder.button(
            text=f"{product['name']} - {product['price']}₽",
            callback_data=f"product_{product['id']}"
        )
    
    builder.button(text='⬅️ Назад', callback_data=f'category_{category_id}')
    builder.button(text='🏠 Главное меню', callback_data='back_to_menu')
    builder.adjust(1)
    
    return builder.as_markup()


def product_card(product: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Карточка товара"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text='➕ В корзину', callback_data=f"add_to_cart_{product['id']}")
    builder.button(text='⬅️ Назад', callback_data=f"category_{product['category_id']}")
    builder.button(text='🏠 Главное меню', callback_data='back_to_menu')
    builder.adjust(1)
    
    return builder.as_markup()


def cart_menu() -> InlineKeyboardMarkup:
    """Кнопки корзины"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text='🗑 Очистить корзину', callback_data='clear_cart')
    builder.button(text='✅ Оформить заказ', callback_data='checkout')
    builder.button(text='⬅️ Назад', callback_data='back_to_menu')
    builder.adjust(1)
    
    return builder.as_markup()


def admin_panel() -> InlineKeyboardMarkup:
    """Инлайн-кнопки админ-панели"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text='📊 Статистика', callback_data='admin_stats')
    builder.button(text='➕ Добавить категорию', callback_data='admin_add_category')
    builder.button(text='➕ Добавить товар', callback_data='admin_add_product')
    builder.button(text='🗑 Удалить товар', callback_data='admin_delete_product')
    builder.button(text='⬅️ Назад', callback_data='back_to_menu')
    builder.adjust(1)
    
    return builder.as_markup()


def admin_categories(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Список категорий для админа"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.button(
            text=category['name'],
            callback_data=f"admin_cat_{category['id']}"
        )
    
    builder.button(text='⬅️ Назад', callback_data='admin_panel')
    builder.adjust(1)
    
    return builder.as_markup()


def admin_products(products: List[Dict[str, Any]], category_id: int) -> InlineKeyboardMarkup:
    """Список товаров категории для админа"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        builder.button(
            text=f"🗑 {product['name']}",
            callback_data=f"admin_del_product_{product['id']}"
        )
    
    builder.button(text='⬅️ Назад', callback_data='admin_panel')
    builder.adjust(1)
    
    return builder.as_markup()


def cancel_fsm() -> InlineKeyboardMarkup:
    """Кнопка отмены FSM"""
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data='cancel_fsm')
    return builder.as_markup()


def confirm_delete(product_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Да, удалить', callback_data=f'confirm_del_{product_id}')
    builder.button(text='❌ Нет', callback_data='admin_panel')
    builder.adjust(1)
    return builder.as_markup()
