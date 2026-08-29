from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from database import Database
from keyboards import categories_keyboard, products_keyboard, product_card_keyboard

router = Router()
db = Database()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message):
    """Показать все категории товаров"""
    kb = await categories_keyboard(db)
    await message.answer("🛍 Выберите категорию:", reply_markup=kb)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery):
    """Вернуться к списку категорий"""
    await callback.answer()
    try:
        kb = await categories_keyboard(db)
        await callback.message.edit_text("🛍 Выберите категорию:", reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery):
    """Показать товары выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    try:
        kb = await products_keyboard(category_id, db)
        await callback.message.edit_text("📦 Выберите товар:", reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery):
    """Показать карточку товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return
    
    try:
        kb = await product_card_keyboard(product_id)
        text = (
            f"📦 <b>{product['name']}</b>\n\n"
            f"📝 {product['description']}\n\n"
            f"💰 Цена: <b>{product['price']} ₽</b>"
        )
        await callback.message.edit_text(text, reply_markup=kb, parse_mode='HTML')
    except Exception:
        pass


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    await callback.answer()
    product_id = int(callback.data.split('_')[3])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer('✅ Товар добавлен в корзину!', show_alert=False)
