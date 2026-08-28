from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import categories_kb, products_kb, product_detail_kb, main_menu_kb
from config import settings

router = Router()


class ProductStates(StatesGroup):
    """Состояния для FSM при работе с товарами"""
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, db: Database):
    """Показ категорий товаров"""
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "📭 Каталог пуст. Товары появятся позже!",
            reply_markup=main_menu_kb(is_admin=message.from_user.id in settings.ADMIN_IDS)
        )
        return
    
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_kb(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database):
    """Показ товаров в выбранной категории"""
    await callback.answer()
    
    category_id = int(callback.data.split('_')[1])
    products = await db.get_products(category_id=category_id)
    
    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=categories_kb(await db.get_categories())
        )
        return
    
    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_kb(products)
    )


@router.callback_query(F.data.startswith('prod_'))
async def show_product_detail(callback: CallbackQuery, db: Database):
    """Показ детальной информации о товаре"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=categories_kb(await db.get_categories())
        )
        return
    
    await callback.message.edit_text(
        f"📦 <b>{product.get('title', 'Товар')}</b>\n\n"
        f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
        f"💰 Цена: {product.get('price', 0)}₽",
        reply_markup=product_detail_kb(product_id),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавление товара в корзину"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[3])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer("✅ Добавлено в корзину!", show_alert=True)


@router.callback_query(F.data == 'back_main')
async def back_to_main(callback: CallbackQuery, db: Database):
    """Возврат в главное меню"""
    await callback.answer()
    
    is_admin = callback.from_user.id in settings.ADMIN_IDS
    await callback.message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )
    await callback.message.delete()


@router.callback_query(F.data == 'back_categories')
async def back_to_categories(callback: CallbackQuery, db: Database):
    """Возврат к списку категорий"""
    await callback.answer()
    
    categories = await db.get_categories()
    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=categories_kb(categories)
    )
