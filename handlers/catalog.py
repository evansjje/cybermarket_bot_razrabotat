# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards import categories_keyboard, products_keyboard, product_card, main_menu
from config import settings

router = Router()
db = Database()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message):
    """Показ категорий товаров"""
    await db.connect()
    categories = await db.get_categories()
    await db.close()

    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('category:'))
async def show_products(callback: CallbackQuery):
    """Показ товаров выбранной категории"""
    await callback.answer()

    category_id = int(callback.data.split(':')[1])

    await db.connect()
    products = await db.get_products(category_id=category_id)
    await db.close()

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


@router.callback_query(F.data.startswith('product:'))
async def show_product_card(callback: CallbackQuery):
    """Показ карточки товара"""
    await callback.answer()

    product_id = int(callback.data.split(':')[1])

    await db.connect()
    product = await db.get_product_by_id(product_id)
    await db.close()

    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return

    text = (
        f"🛍 <b>{product.get('title', 'Товар')}</b>\n\n"
        f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
        f"💰 Цена: <b>{product.get('price', 0)}₽</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=product_card(product_id)
    )


@router.callback_query(F.data == 'back_to_catalog')
async def back_to_catalog(callback: CallbackQuery):
    """Возврат к списку категорий"""
    await callback.answer()

    await db.connect()
    categories = await db.get_categories()
    await db.close()

    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery):
    """Возврат к списку категорий"""
    await callback.answer()

    await db.connect()
    categories = await db.get_categories()
    await db.close()

    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()

    user = callback.from_user
    is_admin = user.id in settings.ADMIN_IDS

    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=main_menu(is_admin)
    )


@router.callback_query(F.data.startswith('add_to_cart:'))
async def add_to_cart(callback: CallbackQuery):
    """Добавление товара в корзину"""
    await callback.answer("✅ Добавлено!")

    product_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id

    await db.connect()
    await db.add_to_cart(user_id, product_id)
    await db.close()

    # Показываем обновлённую карточку товара
    await db.connect()
    product = await db.get_product_by_id(product_id)
    await db.close()

    if product:
        text = (
            f"🛍 <b>{product.get('title', 'Товар')}</b>\n\n"
            f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
            f"💰 Цена: <b>{product.get('price', 0)}₽</b>\n\n"
            f"✅ Товар добавлен в корзину!"
        )

        try:
            await callback.message.edit_text(
                text,
                reply_markup=product_card(product_id)
            )
        except Exception:
            pass
