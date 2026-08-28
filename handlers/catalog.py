# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import (
    CategoryCallback,
    ProductCallback,
    get_categories_keyboard,
    get_products_keyboard,
    get_main_menu
)
from config import settings

router = Router()

@router.message(F.text == '🛍 Каталог')
async def show_catalog(message: Message, db: Database):
    categories = await db.get_categories()
    user_id = message.from_user.id
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=get_categories_keyboard(categories, user_id)
    )

@router.callback_query(CategoryCallback.filter(F.action == 'view'))
async def show_category_products(callback: CallbackQuery, callback_data: CategoryCallback, db: Database):
    await callback.answer()
    cat_id = callback_data.cat_id
    products = await db.get_products(category_id=cat_id)
    user_id = callback.from_user.id
    
    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=get_categories_keyboard(await db.get_categories(), user_id)
        )
        return
    
    await callback.message.edit_text(
        f"📦 Товары в категории:\n\nВыберите товар:",
        reply_markup=get_products_keyboard(products, cat_id, user_id)
    )

@router.callback_query(ProductCallback.filter(F.action == 'view'))
async def show_product_details(callback: CallbackQuery, callback_data: ProductCallback, db: Database):
    await callback.answer()
    product = await db.get_product_by_id(callback_data.product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    user_id = callback.from_user.id
    text = (
        f"📦 <b>{product.get('title', 'Без названия')}</b>\n\n"
        f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
        f"💰 Цена: {product.get('price', 0)} ₽"
    )
    
    from keyboards import get_product_detail_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=get_product_detail_keyboard(product.get('id'), callback_data.cat_id, user_id),
        parse_mode='HTML'
    )

@router.callback_query(ProductCallback.filter(F.action == 'add_to_cart'))
async def add_to_cart(callback: CallbackQuery, callback_data: ProductCallback, db: Database):
    await callback.answer()
    user_id = callback.from_user.id
    product_id = callback_data.product_id
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer('✅ Добавлено в корзину!', show_alert=False)

@router.callback_query(CategoryCallback.filter(F.action == 'back'))
async def back_to_categories(callback: CallbackQuery, db: Database):
    await callback.answer()
    categories = await db.get_categories()
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=get_categories_keyboard(categories, user_id)
    )

@router.callback_query(ProductCallback.filter(F.action == 'back'))
async def back_to_products(callback: CallbackQuery, callback_data: ProductCallback, db: Database):
    await callback.answer()
    cat_id = callback_data.cat_id
    products = await db.get_products(category_id=cat_id)
    user_id = callback.from_user.id
    
    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=get_categories_keyboard(await db.get_categories(), user_id)
        )
        return
    
    await callback.message.edit_text(
        "📦 Товары в категории:\n\nВыберите товар:",
        reply_markup=get_products_keyboard(products, cat_id, user_id)
    )
