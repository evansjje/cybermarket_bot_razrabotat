from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from typing import List, Dict, Any

from config import settings
from database import Database
from keyboards import (
    get_catalog_keyboard,
    get_products_keyboard,
    get_product_keyboard,
    get_cart_keyboard,
    get_main_menu
)

router = Router()
db = Database()


class CartStates(StatesGroup):
    """Состояния для корзины"""
    viewing_cart = State()


async def get_categories() -> List[str]:
    """Получает список категорий товаров"""
    if not db.connection:
        await db.connect()
    cursor = await db.connection.execute(
        "SELECT DISTINCT category FROM products WHERE is_active = 1 ORDER BY category"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def get_products_by_category(category: str) -> List[Dict[str, Any]]:
    """Получает товары по категории"""
    if not db.connection:
        await db.connect()
    cursor = await db.connection.execute(
        "SELECT id, name, description, price, category FROM products WHERE category = ? AND is_active = 1",
        (category,)
    )
    rows = await cursor.fetchall()
    products = []
    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "category": row[4]
        })
    return products


async def get_product_by_id(product_id: int) -> Dict[str, Any]:
    """Получает товар по ID"""
    if not db.connection:
        await db.connect()
    cursor = await db.connection.execute(
        "SELECT id, name, description, price, category, file_path, download_link FROM products WHERE id = ? AND is_active = 1",
        (product_id,)
    )
    row = await cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "category": row[4],
            "file_path": row[5],
            "download_link": row[6]
        }
    return None


async def add_to_cart(user_id: int, product_id: int) -> bool:
    """Добавляет товар в корзину"""
    if not db.connection:
        await db.connect()
    
    # Проверяем, существует ли пользователь
    cursor = await db.connection.execute(
        "SELECT id FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    user = await cursor.fetchone()
    
    if not user:
        return False
    
    # Проверяем, есть ли уже такой товар в корзине
    cursor = await db.connection.execute(
        "SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?",
        (user[0], product_id)
    )
    existing = await cursor.fetchone()
    
    if existing:
        # Увеличиваем количество
        await db.connection.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE id = ?",
            (existing[0],)
        )
    else:
        # Добавляем новый товар
        await db.connection.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)",
            (user[0], product_id)
        )
    
    await db.connection.commit()
    return True


async def get_cart_items(user_id: int) -> List[Dict[str, Any]]:
    """Получает содержимое корзины пользователя"""
    if not db.connection:
        await db.connect()
    
    cursor = await db.connection.execute(
        """SELECT p.id, p.name, p.price, c.quantity 
           FROM cart c 
           JOIN products p ON c.product_id = p.id 
           WHERE c.user_id = (SELECT id FROM users WHERE telegram_id = ?)""",
        (user_id,)
    )
    rows = await cursor.fetchall()
    
    items = []
    for row in rows:
        items.append({
            "product_id": row[0],
            "name": row[1],
            "price": row[2],
            "quantity": row[3]
        })
    return items


async def remove_from_cart(user_id: int, product_id: int) -> bool:
    """Удаляет товар из корзины"""
    if not db.connection:
        await db.connect()
    
    cursor = await db.connection.execute(
        """DELETE FROM cart 
           WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?) 
           AND product_id = ?""",
        (user_id, product_id)
    )
    await db.connection.commit()
    return cursor.rowcount > 0


async def clear_cart(user_id: int) -> bool:
    """Очищает корзину пользователя"""
    if not db.connection:
        await db.connect()
    
    cursor = await db.connection.execute(
        """DELETE FROM cart 
           WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)""",
        (user_id,)
    )
    await db.connection.commit()
    return cursor.rowcount > 0


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    """Показывает каталог товаров"""
    categories = await get_categories()
    if not categories:
        await message.answer("Каталог пуст. Загляните позже!")
        return
    
    await message.answer(
        "📂 Выберите категорию товаров:",
        reply_markup=get_catalog_keyboard(categories)
    )


@router.callback_query(F.data.startswith("category:"))
async def show_category(callback: CallbackQuery):
    """Показывает товары в выбранной категории"""
    category = callback.data.split(":", 1)[1]
    products = await get_products_by_category(category)
    
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📂 Категория: {category}\n\nВыберите товар:",
        reply_markup=get_products_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery):
    """Показывает подробную информацию о товаре"""
    product_id = int(callback.data.split(":", 1)[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Проверяем, есть ли товар в корзине
    cart_items = await get_cart_items(callback.from_user.id)
    in_cart = any(item["product_id"] == product_id for item in cart_items)
    
    text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>\n"
        f"📂 Категория: {product['category']}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_product_keyboard(product_id, in_cart),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "add_to_cart")
async def add_product_to_cart(callback: CallbackQuery):
    """Добавляет товар в корзину"""
    # Получаем ID товара из сообщения
    # Для этого нужно передавать product_id в callback_data
    # В реальном проекте лучше использовать FSM или хранить состояние
    # Здесь мы используем упрощенный подход - получаем из текста сообщения
    
    # В реальном проекте нужно передавать product_id через callback_data
    # Например: "add_to_cart:123"
    # Здесь для простоты используем заглушку
    await callback.answer("Функция добавления в корзину требует передачи ID товара", show_alert=True)


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_product_to_cart_with_id(callback: CallbackQuery):
    """Добавляет товар в корзину по ID"""
    product_id = int(callback.data.split(":", 1)[1])
    success = await add_to_cart(callback.from_user.id, product_id)
    
    if success:
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    else:
        await callback.answer("❌ Не удалось добавить товар", show_alert=True)


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показывает корзину пользователя"""
    cart_items = await get_cart_items(message.from_user.id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return
    
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        text += f"📦 {item['name']} x{item['quantity']} = {item['price'] * item['quantity']}₽\n"
    text += f"\n💰 <b>Итого: {total}₽</b>"
    
    await message.answer(
        text,
        reply_markup=get_cart_keyboard(cart_items),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_product_from_cart(callback: CallbackQuery):
    """Удаляет товар из корзины"""
    product_id = int(callback.data.split(":", 1)[1])
    success = await remove_from_cart(callback.from_user.id, product_id)
    
    if success:
        await callback.answer("🗑 Товар удален из корзины", show_alert=True)
        # Обновляем корзину
        cart_items = await get_cart_items(callback.from_user.id)
        if cart_items:
            total = sum(item["price"] * item["quantity"] for item in cart_items)
            text = "🛒 <b>Ваша корзина:</b>\n\n"
            for item in cart_items:
                text += f"📦 {item['name']} x{item['quantity']} = {item['price'] * item['quantity']}₽\n"
            text += f"\n💰 <b>Итого: {total}₽</b>"
            await callback.message.edit_text(
                text,
                reply_markup=get_cart_keyboard(cart_items),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text("🛒 Ваша корзина пуста!")
    else:
        await callback.answer("❌ Не удалось удалить товар", show_alert=True)


@router.callback_query(F.data == "clear_cart")
async def clear_user_cart(callback: CallbackQuery):
    """Очищает корзину пользователя"""
    success = await clear_cart(callback.from_user.id)
    
    if success:
        await callback.message.edit_text("🛒 Корзина очищена!")
        await callback.answer()
    else:
        await callback.answer("❌ Не удалось очистить корзину", show_alert=True)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Возвращает к списку категорий"""
    categories = await get_categories()
    await callback.message.edit_text(
        "📂 Выберите категорию товаров:",
        reply_markup=get_catalog_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возвращает в главное меню"""
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Команда /catalog - показывает каталог"""
    await show_catalog(message)


@router.message(Command("cart"))
async def cmd_cart(message: Message):
    """Команда /cart - показывает корзину"""
    await show_cart(message)
