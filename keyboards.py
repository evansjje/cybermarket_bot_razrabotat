from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import settings
from database import get_connection


async def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    return await get_main_menu(user_id)


async def get_cart_actions_keyboard(product_id: int, count: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➖", callback_data=f"dec_{product_id}")
    builder.button(text=f"{count} шт", callback_data="noop")
    builder.button(text="➕", callback_data=f"inc_{product_id}")
    builder.button(text="❌ Удалить", callback_data=f"del_{product_id}")
    builder.adjust(3, 1)
    return builder.as_markup()


async def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="🛒 Корзина"))
    builder.row(KeyboardButton(text="👥 Рефералка"), KeyboardButton(text="⭐ Отзывы"))
    builder.row(KeyboardButton(text="🆘 Поддержка"))
    if user_id in settings.ADMIN_IDS:
        builder.row(KeyboardButton(text="⚡ Админ-панель"))
    return builder.as_markup(resize_keyboard=True)


async def get_categories_keyboard() -> InlineKeyboardMarkup:
    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT id, name FROM categories ORDER BY id")
        categories = await cursor.fetchall()
    finally:
        await conn.close()

    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category["name"],
            callback_data=f"cat_{category['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


async def get_products_keyboard(category_id: int) -> InlineKeyboardMarkup:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT id, title, price FROM products WHERE category_id = ? ORDER BY id",
            (category_id,)
        )
        products = await cursor.fetchall()
    finally:
        await conn.close()

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['title']} — {product['price']}₽",
            callback_data=f"prod_{product['id']}"
        )
    builder.button(text="🔙 Назад", callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


async def get_product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ В корзину", callback_data=f"add_{product_id}")
    builder.button(text="🔙 Назад", callback_data="back_to_products")
    builder.adjust(1)
    return builder.as_markup()


async def get_cart_keyboard(user_id: int) -> InlineKeyboardMarkup:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT c.product_id, c.count, p.title, p.price
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            """,
            (user_id,)
        )
        items = await cursor.fetchall()
    finally:
        await conn.close()

    builder = InlineKeyboardBuilder()
    for item in items:
        product_id = item["product_id"]
        builder.button(
            text=f"➖ {item['title']}",
            callback_data=f"dec_{product_id}"
        )
        builder.button(
            text=f"{item['count']} шт",
            callback_data="noop"
        )
        builder.button(
            text=f"➕ {item['title']}",
            callback_data=f"inc_{product_id}"
        )
        builder.button(
            text=f"❌ {item['title']}",
            callback_data=f"del_{product_id}"
        )
    if items:
        builder.row(
            InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart"),
            InlineKeyboardButton(text="💳 Оплатить", callback_data="checkout")
        )
    builder.row(InlineKeyboardButton(text="🔙 В каталог", callback_data="back_to_categories"))
    builder.adjust(2)
    return builder.as_markup()


async def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="📦 Список товаров", callback_data="admin_products")
    builder.adjust(1)
    return builder.as_markup()


async def get_admin_products_keyboard() -> InlineKeyboardMarkup:
    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT id, title FROM products ORDER BY id")
        products = await cursor.fetchall()
    finally:
        await conn.close()

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"🗑 {product['title']}",
            callback_data=f"admin_del_{product['id']}"
        )
    builder.button(text="🔙 Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


async def get_reviews_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ Оставить отзыв", callback_data="leave_review")
    builder.adjust(1)
    return builder.as_markup()


async def get_support_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📨 Написать в поддержку", url="https://t.me/support")
    builder.adjust(1)
    return builder.as_markup()
