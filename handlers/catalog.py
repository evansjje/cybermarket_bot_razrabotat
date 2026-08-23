# handlers/catalog.py
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import Database
from keyboards import (
    categories_kb,
    products_kb,
    product_card_kb,
    main_menu_kb
)
from config import settings

router = Router()
db = Database()


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    """Показать список категорий"""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer(
            "📭 Каталог пока пуст. Загляните позже!",
            reply_markup=main_menu_kb(is_admin=message.from_user.id == settings.ADMIN_ID)
        )
        return
    
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_kb(categories)
    )


@router.callback_query(F.data.startswith("cat_"))
async def show_category_products(callback: CallbackQuery):
    """Показать товары выбранной категории"""
    category_id = int(callback.data.split("_")[1])
    
    products = await db.get_products(category_id)
    category = await db.get_category(category_id)
    
    if not products:
        await callback.message.edit_text(
            f"📁 {category['name']}\n\n"
            "😔 В этой категории пока нет товаров.",
            reply_markup=categories_kb(await db.get_categories())
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"📁 {category['name']}\n\n"
        f"Найдено товаров: {len(products)}\n"
        "Выберите товар:",
        reply_markup=products_kb(products, category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product_card(callback: CallbackQuery):
    """Показать карточку товара"""
    product_id = int(callback.data.split("_")[1])
    
    product = await db.get_product(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=categories_kb(await db.get_categories())
        )
        await callback.answer()
        return
    
    # Формируем карточку товара
    card_text = (
        f"🛍 {product['name']}\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📦 В наличии: {product['stock']} шт.\n\n"
        f"Категория: {product['category_name']}"
    )
    
    await callback.message.edit_text(
        card_text,
        reply_markup=product_card_kb(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    # Проверяем наличие товара
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return
    
    if product['stock'] <= 0:
        await callback.answer("😔 Товар закончился!", show_alert=True)
        return
    
    # Добавляем в корзину
    success = await db.add_to_cart(
        user_id=user_id,
        product_id=product_id
    )
    
    if success:
        await callback.answer(
            f"✅ {product['name']} добавлен в корзину!",
            show_alert=True
        )
    else:
        await callback.answer(
            "❌ Ошибка при добавлении в корзину",
            show_alert=True
        )


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    user_id = callback.from_user.id
    is_admin = user_id == settings.ADMIN_ID
    
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    await callback.answer()


@router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Команда /catalog"""
    await show_catalog(message)
