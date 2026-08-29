# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import categories_keyboard, products_keyboard, product_card_keyboard, main_menu
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
async def show_category_products(callback: CallbackQuery, db: Database):
    """Показать товары выбранной категории"""
    await callback.answer()
    
    category_id = int(callback.data.split('_')[1])
    products = await db.get_products(category_id=category_id)
    
    if not products:
        await callback.message.edit_text(
            "😔 В этой категории пока нет товаров.",
            reply_markup=products_keyboard(products)
        )
        return
    
    await callback.message.edit_text(
        "📦 Товары в категории:",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery, db: Database):
    """Показать карточку товара"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=products_keyboard(await db.get_products())
        )
        return
    
    text = (
        f"📦 <b>{product.get('title', 'Без названия')}</b>\n\n"
        f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
        f"💰 Цена: {product.get('price', 0)}₽"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=product_card_keyboard(product_id),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'add_to_cart')
async def add_to_cart(callback: CallbackQuery, db: Database, state: FSMContext):
    """Добавить товар в корзину"""
    await callback.answer()
    
    # Получаем product_id из состояния или из callback_data
    data = await state.get_data()
    product_id = data.get('current_product_id')
    
    if not product_id:
        # Если нет в состоянии, пробуем извлечь из callback_data
        callback_data = callback.data
        if '_' in callback_data:
            parts = callback_data.split('_')
            if len(parts) > 1 and parts[1].isdigit():
                product_id = int(parts[1])
    
    if not product_id:
        await callback.answer("❌ Ошибка добавления", show_alert=True)
        return
    
    user_id = callback.from_user.id
    await db.add_to_cart(user_id, product_id)
    
    await callback.answer("✅ Добавлено в корзину!", show_alert=False)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery, db: Database):
    """Вернуться к списку категорий"""
    await callback.answer()
    
    categories = await db.get_categories()
    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data == 'back_to_products')
async def back_to_products(callback: CallbackQuery, db: Database, state: FSMContext):
    """Вернуться к списку товаров"""
    await callback.answer()
    
    data = await state.get_data()
    category_id = data.get('current_category_id')
    
    if category_id:
        products = await db.get_products(category_id=category_id)
        await callback.message.edit_text(
            "📦 Товары в категории:",
            reply_markup=products_keyboard(products)
        )
    else:
        categories = await db.get_categories()
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
