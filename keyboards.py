from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import settings


def main_menu_kb(user_id: int = None) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if user_id and user_id in settings.ADMIN_IDS:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def admin_menu_kb() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Добавить товар'))
    builder.row(KeyboardButton(text='📦 Список товаров'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)


def categories_kb(categories: list) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat['name'], callback_data=f'cat_{cat["id"]}')
    builder.adjust(1)
    return builder.as_markup()


def products_kb(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(text=f"{prod['title']} — {prod['price']}₽", callback_data=f'prod_{prod["id"]}')
    builder.button(text='⬅️ Назад', callback_data='back_to_categories')
    builder.adjust(1)
    return builder.as_markup()


def product_card_kb(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ В корзину', callback_data=f'add_{product_id}')
    builder.button(text='⬅️ Назад', callback_data='back_to_products')
    builder.adjust(1)
    return builder.as_markup()


def cart_kb() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить корзину', callback_data='clear_cart')
    builder.button(text='💳 Оплатить', callback_data='checkout')
    builder.button(text='⬅️ В меню', callback_data='back_to_menu')
    builder.adjust(1)
    return builder.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура списка товаров для админа"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"❌ {prod['title']} ({prod['price']}₽)",
            callback_data=f'del_{prod["id"]}'
        )
    builder.button(text='⬅️ Назад', callback_data='back_to_admin')
    builder.adjust(1)
    return builder.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ-панель"""
    builder = InlineKeyboardBuilder()
    builder.button(text='⬅️ Назад', callback_data='back_to_admin')
    return builder.as_markup()
