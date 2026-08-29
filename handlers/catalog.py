from aiogram import Router, types, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import categories_keyboard, products_keyboard, main_menu
from config import settings

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, db: Database) -> None:
    """Показ списка категорий"""
    categories = await db.get_categories()
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database) -> None:
    """Показ товаров выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    products = await db.get_products(category_id=category_id)
    
    if not products:
        await callback.message.answer("📭 В этой категории пока нет товаров.")
        return
    
    await callback.message.answer(
        "📦 Выберите товар:",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery, db: Database) -> None:
    """Показ карточки товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer("❌ Товар не найден.")
        return
    
    text = (
        f"📦 <b>{product.get('title', 'Без названия')}</b>\n\n"
        f"📝 {product.get('description', 'Описание отсутствует')}\n\n"
        f"💰 Цена: <b>{product.get('price', 0)} ₽</b>"
    )
    
    from keyboards import product_card_keyboard
    await callback.message.answer(
        text,
        reply_markup=product_card_keyboard(product_id)
    )


@router.callback_query(F.data == 'add_to_cart')
async def add_to_cart(callback: CallbackQuery, db: Database) -> None:
    """Добавление товара в корзину"""
    await callback.answer()
    
    # Получаем product_id из callback_data
    # В реальном коде нужно передавать product_id в callback_data
    # Например: add_to_cart_{product_id}
    # Здесь используем заглушку, но в реальном проекте нужно передавать ID
    product_id = int(callback.data.split('_')[-1])
    
    user_id = callback.from_user.id
    await db.add_to_cart(user_id, product_id)
    
    await callback.answer("✅ Добавлено!", show_alert=False)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery, db: Database) -> None:
    """Возврат к списку категорий"""
    await callback.answer()
    categories = await db.get_categories()
    
    try:
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('back_to_products_'))
async def back_to_products(callback: CallbackQuery, db: Database) -> None:
    """Возврат к списку товаров категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[-1])
    products = await db.get_products(category_id=category_id)
    
    try:
        await callback.message.edit_text(
            "📦 Выберите товар:",
            reply_markup=products_keyboard(products)
        )
    except Exception:
        pass
