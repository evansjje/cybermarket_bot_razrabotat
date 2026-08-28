# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from database import Database
from keyboards import categories_keyboard, products_keyboard, main_menu
from config import settings

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, db: Database) -> None:
    """Показ списка категорий товаров."""
    categories = await db.get_categories()
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database) -> None:
    """Показ товаров выбранной категории."""
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


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery, db: Database) -> None:
    """Показ карточки товара."""
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
        f"💰 Цена: {product.get('price', 0)}₽\n\n"
        f"📝 Описание:\n{product.get('desc', 'Нет описания')}"
    )
    
    from keyboards import product_card_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=product_card_keyboard(product_id),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'add_to_cart')
async def add_to_cart(callback: CallbackQuery, db: Database) -> None:
    """Добавление товара в корзину."""
    await callback.answer()
    
    # Получаем product_id из callback_data (формат: add_to_cart_{product_id})
    product_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer("✅ Добавлено в корзину!", show_alert=False)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery, db: Database) -> None:
    """Возврат к списку категорий."""
    await callback.answer()
    categories = await db.get_categories()
    try:
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
    except Exception:
        pass
