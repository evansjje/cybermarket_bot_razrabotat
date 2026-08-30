# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import (
    categories_keyboard,
    products_keyboard,
    product_card_keyboard,
    main_menu
)

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message, db: Database):
    """Показ списка категорий."""
    categories = await db.get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст. Загляните позже!")
        return

    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_products(callback: CallbackQuery, db: Database):
    """Показ товаров выбранной категории."""
    await callback.answer()

    try:
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
    except Exception:
        pass


@router.callback_query(F.data.startswith('prod_'))
async def show_product_card(callback: CallbackQuery, db: Database):
    """Показ карточки товара."""
    await callback.answer()

    try:
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
            f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
            f"💰 Цена: <b>{product.get('price', 0)}₽</b>"
        )

        await callback.message.edit_text(
            text,
            reply_markup=product_card_keyboard(product_id),
            parse_mode='HTML'
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('add_'))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавление товара в корзину."""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[1])
        user_id = callback.from_user.id

        await db.add_to_cart(user_id, product_id)
        await callback.answer("✅ Добавлено в корзину!", show_alert=False)
    except Exception:
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)


@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery, db: Database):
    """Возврат к списку категорий."""
    await callback.answer()

    try:
        categories = await db.get_categories()
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_products')
async def back_to_products(callback: CallbackQuery, db: Database):
    """Возврат к списку товаров."""
    await callback.answer()

    try:
        # Получаем категорию из текущего сообщения (упрощенно - показываем все товары)
        products = await db.get_products()
        if products:
            await callback.message.edit_text(
                "📦 Выберите товар:",
                reply_markup=products_keyboard(products)
            )
        else:
            await callback.message.edit_text(
                "📭 Товаров нет.",
                reply_markup=categories_keyboard(await db.get_categories())
            )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await callback.answer()
    await state.clear()

    try:
        from config import settings
        is_admin = callback.from_user.id in settings.ADMIN_IDS
        await callback.message.delete()
        await callback.message.answer(
            "🏠 Главное меню:",
            reply_markup=main_menu(is_admin)
        )
    except Exception:
        pass
