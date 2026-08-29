from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import categories_keyboard, products_keyboard, product_card_keyboard, main_menu

router = Router()


@router.callback_query(F.data == 'catalog')
async def show_categories(callback: CallbackQuery, db: Database):
    """Показать категории товаров"""
    await callback.answer()
    try:
        keyboard = await categories_keyboard(db)
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=keyboard
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database):
    """Показать товары выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    try:
        keyboard = await products_keyboard(category_id, db)
        await callback.message.edit_text(
            "📦 Выберите товар:",
            reply_markup=keyboard
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery, db: Database):
    """Показать карточку товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return

    try:
        keyboard = await product_card_keyboard(product_id)
        await callback.message.edit_text(
            f"📦 <b>{product['name']}</b>\n\n"
            f"📝 {product['description']}\n\n"
            f"💰 Цена: {product['price']} ₽",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавить товар в корзину"""
    await callback.answer()
    product_id = int(callback.data.split('_')[3])
    user_id = callback.from_user.id

    await db.add_to_cart(user_id, product_id)
    await callback.answer('✅ Товар добавлен в корзину!', show_alert=False)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery, db: Database):
    """Вернуться к категориям"""
    await callback.answer()
    try:
        keyboard = await categories_keyboard(db)
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=keyboard
        )
    except Exception:
        pass


@router.message(F.text == '🛍 Каталог')
async def catalog_button(message: Message, db: Database, state: FSMContext):
    """Обработка нажатия кнопки Каталог"""
    await state.clear()
    keyboard = await categories_keyboard(db)
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=keyboard
    )
