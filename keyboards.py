from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database import Database


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='➕ В корзину',
        callback_data=f'add_{product_id}'
    ))
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='back_to_products'
    ))
    return builder.as_markup()


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Категория'))
    builder.row(KeyboardButton(text='➕ Товар'), KeyboardButton(text='📦 Товары'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)


async def categories_keyboard(db: Database) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    categories = await db.get_categories()
    for cat in categories:
        builder.row(InlineKeyboardButton(
            text=cat['name'],
            callback_data=f'cat_{cat["id"]}'
        ))
    return builder.as_markup()


async def products_keyboard(category_id: int, db: Database) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    products = await db.get_products(category_id)
    for prod in products:
        builder.row(InlineKeyboardButton(
            text=prod['name'],
            callback_data=f'prod_{prod["id"]}'
        ))
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='back_to_categories'
    ))
    return builder.as_markup()


def product_card(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='➕ В корзину',
        callback_data=f'add_{product_id}'
    ))
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='back_to_products'
    ))
    return builder.as_markup()


async def delete_products_keyboard(db: Database) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    products = await db.get_products()
    for prod in products:
        builder.row(InlineKeyboardButton(
            text=f'❌ {prod["name"]}',
            callback_data=f'del_{prod["id"]}'
        ))
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='back_to_admin'
    ))
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart'),
        InlineKeyboardButton(text='✅ Оформить', callback_data='checkout')
    )
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='back_to_menu'
    ))
    return builder.as_markup()
