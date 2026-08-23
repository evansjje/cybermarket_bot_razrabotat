# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import (
    categories_kb,
    products_kb,
    product_card_kb,
    main_menu_kb,
    back_to_categories_kb
)
from config import settings

router = Router()
db = Database()


class CatalogStates(StatesGroup):
    """Состояния для каталога."""
    viewing_category = State()
    viewing_product = State()


@router.message(F.text == "🛍 Каталог")
async def show_categories(message: Message, state: FSMContext):
    """Показать список категорий."""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer(
            "📭 Каталог пуст. Товары появятся позже!",
            reply_markup=main_menu_kb(is_admin=message.from_user.id == settings.ADMIN_ID)
        )
        return
    
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_kb(categories)
    )
    await state.set_state(CatalogStates.viewing_category)


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery, state: FSMContext):
    """Показать товары выбранной категории."""
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products(category_id)
    
    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=back_to_categories_kb()
        )
        return
    
    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_kb(products, category_id)
    )
    await state.update_data(category_id=category_id)
    await state.set_state(CatalogStates.viewing_category)


@router.callback_query(F.data.startswith("prod_"))
async def show_product_card(callback: CallbackQuery, state: FSMContext):
    """Показать карточку товара."""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    # Формируем текст карточки товара
    card_text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>\n"
        f"📊 В наличии: {product['stock']} шт.\n\n"
        f"Категория: {product['category_name']}"
    )
    
    await callback.message.edit_text(
        card_text,
        reply_markup=product_card_kb(product_id),
        parse_mode="HTML"
    )
    await state.update_data(product_id=product_id)
    await state.set_state(CatalogStates.viewing_product)


@router.callback_query(F.data == "add_to_cart")
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавить товар в корзину."""
    data = await state.get_data()
    product_id = data.get("product_id")
    
    if not product_id:
        await callback.answer("❌ Ошибка: товар не выбран", show_alert=True)
        return
    
    user_id = callback.from_user.id
    
    # Проверяем наличие товара
    product = await db.get_product(product_id)
    if not product or product["stock"] <= 0:
        await callback.answer("❌ Товар закончился", show_alert=True)
        return
    
    # Добавляем в корзину
    success = await db.add_to_cart(user_id, product_id)
    
    if success:
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    else:
        await callback.answer("❌ Ошибка при добавлении в корзину", show_alert=True)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Вернуться к списку категорий."""
    categories = await db.get_categories()
    
    if categories:
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_kb(categories)
        )
    else:
        await callback.message.edit_text(
            "📭 Каталог пуст.",
            reply_markup=main_menu_kb(is_admin=callback.from_user.id == settings.ADMIN_ID)
        )
    
    await state.set_state(CatalogStates.viewing_category)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню."""
    await state.clear()
    is_admin = callback.from_user.id == settings.ADMIN_ID
    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.callback_query(F.data.startswith("page_"))
async def paginate_products(callback: CallbackQuery, state: FSMContext):
    """Пагинация товаров в категории."""
    data = await state.get_data()
    category_id = data.get("category_id")
    
    if not category_id:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    page = int(callback.data.split("_")[1])
    products = await db.get_products(category_id)
    
    if products:
        await callback.message.edit_text(
            "📦 Выберите товар:",
            reply_markup=products_kb(products, category_id, page=page)
        )
