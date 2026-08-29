from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Главное меню
def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина'))
    builder.row(KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы'))
    builder.row(KeyboardButton(text='🆘 Поддержка'))
    if is_admin:
        builder.row(KeyboardButton(text='⚡ Админ-панель'))
    return builder.as_markup(resize_keyboard=True)

# Алиас для main_menu
def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    return main_menu_kb(is_admin)

# Меню админки
def admin_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='📊 Статистика'), KeyboardButton(text='➕ Категория'))
    builder.row(KeyboardButton(text='➕ Товар'), KeyboardButton(text='📦 Товары'))
    builder.row(KeyboardButton(text='⬅️ Назад'))
    return builder.as_markup(resize_keyboard=True)

# Инлайн-кнопки карточки товара
def product_card_buttons(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='➕ В корзину', callback_data=f'add_to_cart:{product_id}'))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data=f'category:{category_id}'))
    return builder.as_markup()

# Инлайн-кнопки списка товаров для удаления
def delete_product_buttons(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f'❌ {product["name"]}',
            callback_data=f'delete_product:{product["id"]}'
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_products_back'))
    return builder.as_markup()

# Инлайн-кнопки категорий
def categories_buttons(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(
            text=f'📂 {category["name"]}',
            callback_data=f'category:{category["id"]}'
        ))
    return builder.as_markup()

# Инлайн-кнопки товаров в категории
def products_buttons(products: list, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f'🛍 {product["name"]} — {product["price"]}₽',
            callback_data=f'product:{product["id"]}'
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='catalog'))
    return builder.as_markup()

# Кнопки корзины
def cart_buttons() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='🗑 Очистить', callback_data='clear_cart'),
        InlineKeyboardButton(text='✅ Оформить', callback_data='checkout')
    )
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='catalog'))
    return builder.as_markup()
