# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards import (
    catalog_categories_kb,
    products_kb,
    product_detail_kb,
    main_menu_kb
)

router = Router()
db = Database()


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    """Показать категории товаров"""
    categories = await db.get_categories()
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=catalog_categories_kb(categories)
    )


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    """Показать товары в выбранной категории"""
    category = callback.data.replace("cat_", "")
    products = await db.get_products_by_category(category)
    
    if not products:
        await callback.message.answer(
            "😔 В этой категории пока нет товаров.",
            reply_markup=catalog_categories_kb(await db.get_categories())
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        f"📦 Товары в категории «{category}»:",
        reply_markup=products_kb(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    """Показать детальную информацию о товаре"""
    product_id = int(callback.data.replace("product_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.message.answer(
            "❌ Товар не найден или был удален.",
            reply_markup=main_menu_kb()
        )
        await callback.answer()
        return
    
    product_id, name, description, price, category, file_path, download_link, is_available = product
    
    if not is_available:
        await callback.message.answer(
            f"❌ Товар «{name}» временно недоступен.",
            reply_markup=main_menu_kb()
        )
        await callback.answer()
        return
    
    text = (
        f"📦 <b>{name}</b>\n\n"
        f"📝 {description}\n\n"
        f"💰 Цена: {price} ₽\n"
        f"📂 Категория: {category}"
    )
    
    await callback.message.answer(
        text,
        reply_markup=product_detail_kb(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    product_id = int(callback.data.replace("add_", ""))
    user_id = callback.from_user.id
    
    success = await db.add_to_cart(user_id, product_id)
    
    if success:
        await callback.message.answer(
            "✅ Товар добавлен в корзину!\n"
            "Перейдите в раздел «🛒 Корзина» для оформления заказа.",
            reply_markup=main_menu_kb()
        )
    else:
        await callback.message.answer(
            "❌ Не удалось добавить товар в корзину. Попробуйте позже.",
            reply_markup=main_menu_kb()
        )
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Вернуться к списку категорий"""
    categories = await db.get_categories()
    await callback.message.answer(
        "🛍 Выберите категорию:",
        reply_markup=catalog_categories_kb(categories)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery):
    """Вернуться к списку товаров (заглушка, будет обработано в других местах)"""
    await callback.message.answer(
        "⬅️ Выберите категорию:",
        reply_markup=catalog_categories_kb(await db.get_categories())
    )
    await callback.answer()
