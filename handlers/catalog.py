from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import db
from keyboards import categories_keyboard, products_keyboard
from config import settings

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message):
    """Показ категорий товаров"""
    categories = await db.get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст. Добавьте категории в админ-панели.")
        return

    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery):
    """Показ товаров выбранной категории"""
    await callback.answer()

    category_id = int(callback.data.split('_')[1])
    products = await db.get_products(category_id=category_id)

    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=products_keyboard([])
        )
        return

    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery):
    """Показ карточки товара"""
    await callback.answer()

    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)

    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return

    # Формируем текст карточки товара
    card_text = (
        f"📦 <b>{product['title']}</b>\n\n"
        f"📝 {product['desc'] or 'Описание отсутствует'}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>"
    )

    # Кнопки для карточки товара
    from keyboards import product_card_keyboard
    await callback.message.edit_text(
        card_text,
        reply_markup=product_card_keyboard(product_id),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'add_to_cart')
async def add_to_cart(callback: CallbackQuery):
    """Добавление товара в корзину"""
    await callback.answer()

    # Получаем product_id из callback_data
    # В реальном коде нужно передавать product_id в callback_data
    # Например: add_to_cart_{product_id}
    # Здесь для примера используем заглушку
    product_id = int(callback.data.split('_')[-1]) if '_' in callback.data else None

    if product_id is None:
        await callback.answer("❌ Ошибка добавления", show_alert=True)
        return

    user_id = callback.from_user.id
    await db.add_to_cart(user_id, product_id)
    await callback.answer('✅ Товар добавлен в корзину!', show_alert=False)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery):
    """Возврат к списку категорий"""
    await callback.answer()

    categories = await db.get_categories()
    if not categories:
        await callback.message.edit_text("📭 Каталог пуст.")
        return

    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart_with_id(callback: CallbackQuery):
    """Добавление товара в корзину с ID товара"""
    await callback.answer()

    product_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id

    await db.add_to_cart(user_id, product_id)
    await callback.answer('✅ Товар добавлен в корзину!', show_alert=False)
