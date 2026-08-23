from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database import db
from keyboards import (
    get_catalog_keyboard,
    get_products_keyboard,
    get_product_detail_keyboard,
    get_cart_keyboard,
    get_main_menu
)

router = Router()

class CatalogStates(StatesGroup):
    """Состояния для каталога."""
    viewing_category = State()
    viewing_product = State()


@router.message(F.text == "🛍️ Каталог")
async def show_catalog(message: Message, state: FSMContext):
    """Показывает каталог категорий."""
    await state.clear()
    
    categories = await db.get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст. Загляните позже!")
        return
    
    await message.answer(
        "🛍️ Выберите категорию товаров:",
        reply_markup=get_catalog_keyboard(categories)
    )


@router.callback_query(F.data.startswith("category:"))
async def show_category_products(callback: CallbackQuery, state: FSMContext):
    """Показывает товары выбранной категории."""
    category = callback.data.split(":", 1)[1]
    
    products = await db.get_products_by_category(category)
    if not products:
        await callback.answer("📭 В этой категории пока нет товаров", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📂 Категория: {category}\n\nВыберите товар:",
        reply_markup=get_products_keyboard(products)
    )
    
    await state.set_state(CatalogStates.viewing_category)
    await state.update_data(category=category)
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery, state: FSMContext):
    """Показывает детальную информацию о товаре."""
    product_id = int(callback.data.split(":", 1)[1])
    
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    # Формируем описание товара
    description = product['description'] or "Описание отсутствует"
    price = product['price']
    
    text = (
        f"📦 {product['name']}\n\n"
        f"📝 {description}\n\n"
        f"💰 Цена: {price}₽"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_product_detail_keyboard(product_id, price)
    )
    
    await state.set_state(CatalogStates.viewing_product)
    await state.update_data(product_id=product_id)
    await callback.answer()


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавляет товар в корзину."""
    product_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id
    
    # Проверяем, существует ли товар
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    # Добавляем в корзину
    success = await db.add_to_cart(user_id, product_id)
    
    if success:
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=False)
    else:
        await callback.answer("❌ Не удалось добавить товар", show_alert=True)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку категорий."""
    categories = await db.get_categories()
    
    await callback.message.edit_text(
        "🛍️ Выберите категорию товаров:",
        reply_markup=get_catalog_keyboard(categories)
    )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показывает содержимое корзины."""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста")
        return
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    text = "🛒 Ваша корзина:\n\n"
    for item in cart_items:
        text += f"📦 {item['name']} x{item['quantity']} — {item['price'] * item['quantity']}₽\n"
    text += f"\n💰 Итого: {total}₽"
    
    await message.answer(
        text,
        reply_markup=get_cart_keyboard(cart_items)
    )


@router.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: CallbackQuery):
    """Удаляет товар из корзины."""
    product_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id
    
    success = await db.remove_from_cart(user_id, product_id)
    
    if success:
        # Обновляем корзину
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            await callback.message.edit_text("🛒 Ваша корзина пуста")
        else:
            total = sum(item['price'] * item['quantity'] for item in cart_items)
            
            text = "🛒 Ваша корзина:\n\n"
            for item in cart_items:
                text += f"📦 {item['name']} x{item['quantity']} — {item['price'] * item['quantity']}₽\n"
            text += f"\n💰 Итого: {total}₽"
            
            await callback.message.edit_text(
                text,
                reply_markup=get_cart_keyboard(cart_items)
            )
        
        await callback.answer("✅ Товар удален из корзины")
    else:
        await callback.answer("❌ Не удалось удалить товар", show_alert=True)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очищает корзину."""
    user_id = callback.from_user.id
    
    success = await db.clear_cart(user_id)
    
    if success:
        await callback.message.edit_text("🛒 Ваша корзина пуста")
        await callback.answer("✅ Корзина очищена")
    else:
        await callback.answer("❌ Не удалось очистить корзину", show_alert=True)
