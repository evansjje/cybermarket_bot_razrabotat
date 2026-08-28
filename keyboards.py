from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database import get_categories, get_products


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def admin_menu_kb() -> ReplyKeyboardMarkup:
    """Меню админки"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Добавить товар'))
    builder.row(KeyboardButton(text='📦 Управление товарами'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)


async def categories_kb() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    builder = InlineKeyboardBuilder()
    categories = await get_categories()
    for cat in categories:
        builder.button(text=cat['name'], callback_data=f'cat_{cat["id"]}')
    builder.adjust(1)
    return builder.as_markup()


async def products_kb(category_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    builder = InlineKeyboardBuilder()
    products = await get_products(category_id)
    for prod in products:
        builder.button(text=f'{prod["title"]} — {prod["price"]}₽', callback_data=f'prod_{prod["id"]}')
    builder.button(text='⬅️ Назад', callback_data='back_categories')
    builder.adjust(1)
    return builder.as_markup()


def product_card_kb(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ В корзину', callback_data=f'buy_prod:{product_id}')
    builder.button(text='⬅️ Назад', callback_data='back_products')
    builder.adjust(1)
    return builder.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    """Инлайн-кнопки управления товарами в админке"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f'{prod["title"]} — {prod["price"]}₽',
            callback_data=f'admin_prod_{prod["id"]}'
        )
    builder.button(text='⬅️ Назад', callback_data='back_admin')
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-кнопки действий над товаром в админке"""
    builder = InlineKeyboardBuilder()
    builder.button(text='✏️ Цена', callback_data=f'edit_price:{product_id}')
    builder.button(text='📝 Описание', callback_data=f'edit_desc:{product_id}')
    builder.button(text='🗑 Удалить', callback_data=f'del_prod:{product_id}')
    builder.button(text='⬅️ Назад', callback_data='back_admin_products')
    builder.adjust(2, 1)
    return builder.as_markup()


def cart_kb() -> InlineKeyboardMarkup:
    """Инлайн-кнопки корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Очистить корзину', callback_data='clear_cart')
    builder.button(text='💳 Оплатить', callback_data='checkout')
    builder.button(text='⬅️ Назад', callback_data='back_main')
    builder.adjust(1)
    return builder.as_markup()
