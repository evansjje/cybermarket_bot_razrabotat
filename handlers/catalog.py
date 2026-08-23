from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import get_connection
from keyboards import get_categories_keyboard, get_products_keyboard, get_product_card_keyboard

router = Router()


@router.message(F.text == "🛍 Каталог")
async def show_categories(message: Message) -> None:
    """Показать категории товаров"""
    keyboard = await get_categories_keyboard()
    await message.answer("🛍 Выберите категорию:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery) -> None:
    """Показать товары выбранной категории"""
    category_id = int(callback.data.split("_")[1])
    
    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        category = await cursor.fetchone()
        
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        
        cursor = await conn.execute(
            "SELECT id, title, desc, price FROM products WHERE category_id = ? ORDER BY id",
            (category_id,)
        )
        products = await cursor.fetchall()
    finally:
        await conn.close()

    if not products:
        await callback.answer("📭 В этой категории пока нет товаров", show_alert=True)
        return

    keyboard = await get_products_keyboard(category_id)
    await callback.message.edit_text(
        f"📂 Категория: {category['name']}\n\n"
        f"Товаров в категории: {len(products)}\n"
        f"Выберите товар:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product_card(callback: CallbackQuery) -> None:
    """Показать карточку товара"""
    product_id = int(callback.data.split("_")[1])
    
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """SELECT p.*, c.name as category_name 
               FROM products p 
               JOIN categories c ON p.category_id = c.id 
               WHERE p.id = ?""",
            (product_id,)
        )
        product = await cursor.fetchone()
    finally:
        await conn.close()

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    keyboard = await get_product_card_keyboard(product_id)
    await callback.message.edit_text(
        f"📦 {product['title']}\n\n"
        f"📂 Категория: {product['category_name']}\n"
        f"💰 Цена: {product['price']}₽\n\n"
        f"📝 Описание:\n{product['desc']}",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery) -> None:
    """Добавить товар в корзину"""
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    conn = await get_connection()
    try:
        # Проверяем существование товара
        cursor = await conn.execute("SELECT id FROM products WHERE id = ?", (product_id,))
        product = await cursor.fetchone()
        
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        # Добавляем в корзину
        await conn.execute(
            """INSERT INTO cart (user_id, product_id, count) 
               VALUES (?, ?, 1)
               ON CONFLICT(user_id, product_id) 
               DO UPDATE SET count = count + 1""",
            (user_id, product_id)
        )
        await conn.commit()
        
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    finally:
        await conn.close()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery) -> None:
    """Вернуться к списку категорий"""
    keyboard = await get_categories_keyboard()
    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=keyboard
    )
    await callback.answer()
