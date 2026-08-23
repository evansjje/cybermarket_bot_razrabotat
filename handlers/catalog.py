from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import catalog_categories_keyboard, products_keyboard, main_menu_keyboard
from typing import Optional, List, Dict, Any

router = Router()

# Состояния для корзины
class CartStates(StatesGroup):
    viewing_product = State()
    adding_to_cart = State()

# Хранилище корзины (в реальном проекте лучше использовать БД или Redis)
cart_storage: Dict[int, List[Dict[str, Any]]] = {}

# Вспомогательная функция для получения корзины пользователя
def get_user_cart(user_id: int) -> List[Dict[str, Any]]:
    if user_id not in cart_storage:
        cart_storage[user_id] = []
    return cart_storage[user_id]

@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message, db: Database):
    """Показать категории товаров"""
    categories = await db.get_categories()
    if not categories:
        await message.answer("Каталог пуст. Загляните позже!", reply_markup=main_menu_keyboard())
        return
    
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=catalog_categories_keyboard(categories)
    )

@router.callback_query(F.data.startswith("category:"))
async def show_category_products(callback: CallbackQuery, db: Database):
    """Показать товары в категории"""
    category = callback.data.split(":", 1)[1]
    products = await db.get_products_by_category(category)
    
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    # Пагинация (по 5 товаров на страницу)
    page_size = 5
    total_pages = (len(products) + page_size - 1) // page_size
    
    await callback.message.edit_text(
        f"📂 Категория: {category}\n\nВыберите товар:",
        reply_markup=products_keyboard(products[:page_size], category, 0, total_pages)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery, db: Database):
    """Обработка пагинации"""
    _, category, page_str = callback.data.split(":")
    page = int(page_str)
    
    products = await db.get_products_by_category(category)
    page_size = 5
    total_pages = (len(products) + page_size - 1) // page_size
    
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(products))
    page_products = products[start_idx:end_idx]
    
    await callback.message.edit_text(
        f"📂 Категория: {category}\n\nВыберите товар:",
        reply_markup=products_keyboard(page_products, category, page, total_pages)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("product:"))
async def show_product_details(callback: CallbackQuery, db: Database, state: FSMContext):
    """Показать детали товара"""
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Формируем описание товара
    description = product.get("description", "Описание отсутствует")
    price = product.get("price", 0)
    name = product.get("name", "Товар")
    
    text = (
        f"📦 <b>{name}</b>\n\n"
        f"📝 {description}\n\n"
        f"💰 Цена: <b>{price}₽</b>"
    )
    
    # Кнопки для товара
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart:{product_id}"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"category:{product.get('category', '')}")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(CartStates.viewing_product)
    await state.update_data(current_product_id=product_id)
    await callback.answer()

@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавить товар в корзину"""
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    user_id = callback.from_user.id
    cart = get_user_cart(user_id)
    
    # Проверяем, есть ли уже такой товар в корзине
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += 1
            await callback.answer("Товар добавлен в корзину!", show_alert=True)
            return
    
    # Добавляем новый товар
    cart.append({
        "product_id": product_id,
        "name": product["name"],
        "price": product["price"],
        "quantity": 1
    })
    
    await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, db: Database):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart = get_user_cart(user_id)
    
    if not cart:
        await message.answer("🛒 Ваша корзина пуста")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    total_price = sum(item["price"] * item["quantity"] for item in cart)
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    for i, item in enumerate(cart, 1):
        cart_text += (
            f"{i}. {item['name']}\n"
            f"   Цена: {item['price']}₽ × {item['quantity']} = {item['price'] * item['quantity']}₽\n\n"
        )
    
    cart_text += f"<b>Итого: {total_price}₽</b>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Оплатить", callback_data="checkout"),
            InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(cart_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    cart_storage[user_id] = []
    await callback.message.edit_text("🗑 Корзина очищена")
    await callback.answer()

@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, db: Database):
    """Оформление заказа"""
    user_id = callback.from_user.id
    cart = get_user_cart(user_id)
    
    if not cart:
        await callback.answer("Корзина пуста", show_alert=True)
        return
    
    # Здесь будет вызов обработчика оплаты
    # В реальном проекте нужно импортировать и вызвать функцию из handlers/payment.py
    await callback.message.edit_text(
        "💳 Переходим к оплате...\n\n"
        "Сейчас вы будете перенаправлены на страницу оплаты."
    )
    await callback.answer()
