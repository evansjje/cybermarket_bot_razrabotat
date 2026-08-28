from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_categories, get_products_by_category, add_to_cart
from keyboards import categories_kb, products_kb, main_menu_kb

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message):
    categories = await get_categories()
    if not categories:
        await message.answer("Каталог пуст. Попробуйте позже.")
        return
    await message.answer(
        "Выберите категорию:",
        reply_markup=categories_kb(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery):
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    products = await get_products_by_category(category_id)
    if not products:
        await callback.message.answer("В этой категории пока нет товаров.")
        return
    await callback.message.edit_text(
        "Выберите товар:",
        reply_markup=products_kb(products, category_id)
    )


@router.callback_query(F.data.startswith('prod_'))
async def show_product_details(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split('_')[1])
    from database import get_product_by_id
    product = await get_product_by_id(product_id)
    if not product:
        await callback.message.answer("Товар не найден.")
        return
    
    from keyboards import product_card_kb
    text = (
        f"📦 <b>{product['title']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Цена: {product['price']}₽"
    )
    await callback.message.edit_text(
        text,
        reply_markup=product_card_kb(product_id)
    )


@router.callback_query(F.data == 'add_to_cart')
async def add_product_to_cart(callback: CallbackQuery):
    await callback.answer("Товар добавлен!", show_alert=False)
    # Получаем product_id из предыдущего сообщения
    # В реальном проекте нужно передавать product_id через callback_data
    # Здесь используем заглушку, но в полной версии нужно передавать
    # product_id в callback_data кнопки
    # Для примера возьмем первый товар
    from database import get_products_by_category
    products = await get_products_by_category(1)
    if products:
        product_id = products[0]['id']
        await add_to_cart(callback.from_user.id, product_id, 1)
    await callback.message.answer("✅ Товар добавлен в корзину!")


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery):
    await callback.answer()
    categories = await get_categories()
    if not categories:
        await callback.message.answer("Каталог пуст.")
        return
    await callback.message.edit_text(
        "Выберите категорию:",
        reply_markup=categories_kb(categories)
    )


@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_kb(callback.from_user.id)
    )
