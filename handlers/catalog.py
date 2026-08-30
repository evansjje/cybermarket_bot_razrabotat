# handlers/catalog.py
from aiogram import Router, types, F
from aiogram.filters import Command
from database import Database
from keyboards import get_categories_keyboard, get_products_keyboard, get_main_menu
from config import settings
from contextlib import suppress

router = Router()
db = Database()


@router.message(F.text == '🛍 Каталог')
async def show_catalog(message: types.Message):
    """Показ категорий товаров"""
    categories = await db.get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст. Добавьте категории в админ-панели.")
        return

    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=get_categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_category_products(callback: types.CallbackQuery):
    """Показ товаров выбранной категории"""
    await callback.answer()

    try:
        category_id = int(callback.data.split('_')[1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID категории.")
        return

    products = await db.get_products(category_id=category_id)
    if not products:
        with suppress(Exception):
            await callback.message.edit_text(
                "📭 В этой категории пока нет товаров.",
                reply_markup=get_categories_keyboard(await db.get_categories())
            )
        return

    # Формируем текст с товарами
    text = "📦 Товары в категории:\n\n"
    for prod in products:
        text += f"🆔 {prod.get('id')} | {prod.get('title')} — {prod.get('price')}₽\n"

    with suppress(Exception):
        await callback.message.edit_text(
            text,
            reply_markup=get_products_keyboard(products)
        )


@router.callback_query(F.data.startswith('product_'))
async def show_product_card(callback: types.CallbackQuery):
    """Показ карточки товара"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID товара.")
        return

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.message.answer("❌ Товар не найден.")
        return

    text = (
        f"📦 <b>{product.get('title')}</b>\n\n"
        f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
        f"💰 Цена: <b>{product.get('price')}₽</b>"
    )

    from keyboards import get_product_card_keyboard
    with suppress(Exception):
        await callback.message.edit_text(
            text,
            reply_markup=get_product_card_keyboard(product_id),
            parse_mode='HTML'
        )


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: types.CallbackQuery):
    """Добавление товара в корзину"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка: неверный ID товара.", show_alert=True)
        return

    user_id = callback.from_user.id
    await db.add_to_cart(user_id, product_id)

    await callback.answer("✅ Добавлено в корзину!", show_alert=False)

    # Показываем обновлённую карточку товара
    product = await db.get_product_by_id(product_id)
    if product:
        text = (
            f"📦 <b>{product.get('title')}</b>\n\n"
            f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
            f"💰 Цена: <b>{product.get('price')}₽</b>\n\n"
            f"✅ Товар добавлен в корзину!"
        )
        from keyboards import get_product_card_keyboard
        with suppress(Exception):
            await callback.message.edit_text(
                text,
                reply_markup=get_product_card_keyboard(product_id),
                parse_mode='HTML'
            )


@router.callback_query(F.data == 'back_to_catalog')
async def back_to_catalog(callback: types.CallbackQuery):
    """Возврат к списку категорий"""
    await callback.answer()

    categories = await db.get_categories()
    with suppress(Exception):
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=get_categories_keyboard(categories)
        )


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()

    user_id = callback.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    with suppress(Exception):
        await callback.message.delete()

    await callback.message.answer(
        "🏠 Главное меню:",
        reply_markup=get_main_menu(is_admin=is_admin)
    )
