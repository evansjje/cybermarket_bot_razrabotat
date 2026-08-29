from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import Database
from keyboards import categories_keyboard, products_keyboard, main_menu
from config import settings

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, db: Database):
    """Показать все категории товаров"""
    categories = await db.get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст. Товары появятся позже.")
        return

    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database):
    """Показать товары выбранной категории"""
    await callback.answer()
    
    try:
        category_id = int(callback.data.split('_')[1])
        products = await db.get_products(category_id=category_id)
        
        if not products:
            await callback.message.edit_text(
                "📭 В этой категории пока нет товаров.",
                reply_markup=None
            )
            return

        await callback.message.edit_text(
            "📦 Выберите товар:",
            reply_markup=products_keyboard(products)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery, db: Database):
    """Показать карточку товара"""
    await callback.answer()
    
    try:
        product_id = int(callback.data.split('_')[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.message.edit_text(
                "❌ Товар не найден.",
                reply_markup=None
            )
            return

        # Создаем клавиатуру для карточки товара
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='➕ В корзину',
                    callback_data=f'add_{product_id}'
                )
            ],
            [
                InlineKeyboardButton(
                    text='⬅️ Назад',
                    callback_data='back_to_catalog'
                )
            ]
        ])

        await callback.message.edit_text(
            f"📦 <b>{product.get('title', 'Без названия')}</b>\n\n"
            f"💰 Цена: {product.get('price', 0)}₽\n\n"
            f"📝 Описание:\n{product.get('desc', 'Нет описания')}",
            reply_markup=kb,
            parse_mode='HTML'
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('add_'))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавить товар в корзину"""
    await callback.answer()
    
    try:
        product_id = int(callback.data.split('_')[1])
        user_id = callback.from_user.id
        
        await db.add_to_cart(user_id, product_id)
        await callback.answer('✅ Добавлено!')
    except Exception:
        await callback.answer('❌ Ошибка добавления')


@router.callback_query(F.data == 'back_to_catalog')
async def back_to_catalog(callback: CallbackQuery, db: Database):
    """Вернуться к списку категорий"""
    await callback.answer()
    
    try:
        categories = await db.get_categories()
        if categories:
            await callback.message.edit_text(
                "🛍 Выберите категорию:",
                reply_markup=categories_keyboard(categories)
            )
        else:
            await callback.message.edit_text(
                "📭 Каталог пуст.",
                reply_markup=None
            )
    except Exception:
        pass
