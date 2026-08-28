# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import categories_keyboard, products_keyboard, main_menu
from config import settings

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, db: Database):
    """Показать категории товаров"""
    categories = await db.get_categories()
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database):
    """Показать товары в выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    products = await db.get_products(category_id=category_id)
    
    if not products:
        await callback.message.edit_text(
            "😔 В этой категории пока нет товаров.",
            reply_markup=categories_keyboard(await db.get_categories())
        )
        return
    
    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('product_'))
async def show_product_details(callback: CallbackQuery, db: Database):
    """Показать карточку товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=categories_keyboard(await db.get_categories())
        )
        return
    
    text = (
        f"📦 <b>{product.get('title', 'Товар')}</b>\n\n"
        f"{product.get('desc', 'Описание отсутствует')}\n\n"
        f"💰 Цена: <b>{product.get('price', 0)} ₽</b>"
    )
    
    from keyboards import product_card_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=product_card_keyboard(product_id),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавить товар в корзину"""
    await callback.answer()
    product_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer("✅ Добавлено в корзину!", show_alert=False)


@router.callback_query(F.data == 'back_to_catalog')
async def back_to_catalog(callback: CallbackQuery, db: Database):
    """Вернуться к списку категорий"""
    await callback.answer()
    categories = await db.get_categories()
    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu(is_admin=is_admin)
    )
