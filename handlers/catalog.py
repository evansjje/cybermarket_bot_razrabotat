from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import product_card_buttons

router = Router()
db = Database()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, state: FSMContext):
    await state.clear()
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("📭 Каталог пуст. Товары появятся позже.")
        return
    
    text = "🛍 Выберите категорию:\n\n"
    for cat in categories:
        text += f"📁 {cat['name']}\n"
    
    await message.answer(text)


@router.callback_query(F.data.startswith('category:'))
async def show_products(callback: CallbackQuery):
    await callback.answer()
    
    category_id = int(callback.data.split(':')[1])
    products = await db.get_products(category_id)
    
    if not products:
        try:
            await callback.message.edit_text("📭 В этой категории пока нет товаров.")
        except Exception:
            pass
        return
    
    text = "📦 Товары в категории:\n\n"
    for product in products:
        text += f"🆔 {product['id']}. {product['name']}\n"
        text += f"📝 {product['description']}\n"
        text += f"💰 Цена: {product['price']} ₽\n\n"
    
    try:
        await callback.message.edit_text(text)
    except Exception:
        pass


@router.callback_query(F.data.startswith('product:'))
async def show_product_card(callback: CallbackQuery):
    await callback.answer()
    
    product_id = int(callback.data.split(':')[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        try:
            await callback.message.edit_text("❌ Товар не найден.")
        except Exception:
            pass
        return
    
    text = f"🆔 {product['name']}\n\n"
    text += f"📝 {product['description']}\n\n"
    text += f"💰 Цена: {product['price']} ₽"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=product_card_buttons(product['id'], product['category_id'])
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('add_to_cart:'))
async def add_to_cart(callback: CallbackQuery):
    await callback.answer()
    
    product_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    
    await callback.answer('✅ Товар добавлен в корзину!', show_alert=False)
