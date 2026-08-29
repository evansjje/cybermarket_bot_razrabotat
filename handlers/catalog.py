# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import categories_keyboard, products_keyboard

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message) -> None:
    """Показ категорий товаров"""
    categories = await db.get_categories()
    await message.answer(
        '🛍 Выберите категорию:',
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery) -> None:
    """Показ товаров в выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    products = await db.get_products(category_id=category_id)
    
    if not products:
        await callback.message.edit_text(
            '😔 В этой категории пока нет товаров',
            reply_markup=products_keyboard([])
        )
        return
    
    await callback.message.edit_text(
        '📦 Выберите товар:',
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery) -> None:
    """Показ карточки товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text('❌ Товар не найден')
        return
    
    text = (
        f"📦 <b>{product['title']}</b>\n\n"
        f"📝 {product['desc']}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>"
    )
    
    from keyboards import product_card_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=product_card_keyboard(product_id)
    )


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: CallbackQuery) -> None:
    """Добавление товара в корзину"""
    await callback.answer()
    product_id = int(callback.data.split('_')[3])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer('✅ Товар добавлен в корзину!', show_alert=False)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery) -> None:
    """Возврат к списку категорий"""
    await callback.answer()
    categories = await db.get_categories()
    await callback.message.edit_text(
        '🛍 Выберите категорию:',
        reply_markup=categories_keyboard(categories)
    )
