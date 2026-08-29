from aiogram import Router, types, F
from aiogram.types import CallbackQuery, Message
from database import Database
from keyboards import categories_keyboard, products_keyboard, product_card_keyboard, main_menu
from config import settings

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, db: Database) -> None:
    """Показывает список категорий"""
    categories = await db.get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст. Добавьте категории в админ-панели.")
        return
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database) -> None:
    """Показывает товары выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    products = await db.get_products(category_id)
    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=categories_keyboard(await db.get_categories())
        )
        return
    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery, db: Database) -> None:
    """Показывает карточку товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return
    
    text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=product_card_keyboard(product_id),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: CallbackQuery, db: Database) -> None:
    """Добавляет товар в корзину"""
    await callback.answer()
    product_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer('✅ Товар добавлен в корзину!', show_alert=False)


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


@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery) -> None:
    """Возврат в главное меню"""
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    try:
        await callback.message.edit_text(
            "🏠 Главное меню",
            reply_markup=None
        )
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu(is_admin=is_admin)
        )
    except Exception:
        pass
