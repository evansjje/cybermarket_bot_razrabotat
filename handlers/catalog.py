from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_categories, get_products, get_product_by_id, add_to_cart
from keyboards import categories_kb, products_kb, main_menu_kb
from config import settings

router = Router()


class ProductStates(StatesGroup):
    """Состояния для работы с товарами"""
    waiting_for_category = State()
    waiting_for_product = State()


@router.message(F.text == '🛍 Каталог')
async def show_catalog(message: Message):
    """Показ категорий товаров"""
    kb = await categories_kb()
    await message.answer("📂 Выберите категорию:", reply_markup=kb)


@router.callback_query(F.data.startswith('cat_'))
async def show_category_products(callback: CallbackQuery):
    """Показ товаров выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    kb = await products_kb(category_id)
    await callback.message.edit_text("🛍 Товары в категории:", reply_markup=kb)


@router.callback_query(F.data.startswith('prod_'))
async def show_product_details(callback: CallbackQuery):
    """Показ деталей товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return
    
    # Получаем категорию товара для кнопки назад
    category_id = product.get('category_id', 0)
    
    from keyboards import product_card_kb
    kb = await product_card_kb(product_id, category_id)
    
    text = (
        f"📦 <b>{product['title']}</b>\n\n"
        f"📝 {product.get('description', 'Описание отсутствует')}\n\n"
        f"💰 Цена: {product['price']}₽"
    )
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode='HTML')


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_product_to_cart(callback: CallbackQuery):
    """Добавление товара в корзину"""
    await callback.answer("✅ Товар добавлен в корзину!")
    
    product_id = int(callback.data.split('_')[3])
    user_id = callback.from_user.id
    
    await add_to_cart(user_id, product_id)
    
    # Показываем уведомление
    await callback.message.answer("🛒 Товар добавлен в корзину!")


@router.callback_query(F.data == 'back_categories')
async def back_to_categories(callback: CallbackQuery):
    """Возврат к списку категорий"""
    await callback.answer()
    kb = await categories_kb()
    await callback.message.edit_text("📂 Выберите категорию:", reply_markup=kb)


@router.callback_query(F.data == 'back_to_catalog')
async def back_to_catalog(callback: CallbackQuery):
    """Возврат к каталогу из корзины"""
    await callback.answer()
    kb = await categories_kb()
    await callback.message.edit_text("📂 Выберите категорию:", reply_markup=kb)
