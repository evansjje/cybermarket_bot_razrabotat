from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import catalog_keyboard, products_keyboard, product_detail_keyboard, main_menu_keyboard

router = Router()
db = Database()


class CartStates(StatesGroup):
    waiting_for_quantity = State()


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    """Показать категории товаров"""
    categories = await db.get_categories()
    if not categories:
        await message.answer("Каталог пуст. Загляните позже!", reply_markup=main_menu_keyboard())
        return
    
    await message.answer(
        "🛍 Выберите категорию товаров:",
        reply_markup=catalog_keyboard(categories)
    )


@router.callback_query(F.data.startswith("category:"))
async def show_category_products(callback: CallbackQuery):
    """Показать товары в выбранной категории"""
    category = callback.data.split(":", 1)[1]
    products = await db.get_products_by_category(category)
    
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📦 Товары в категории «{category}»:",
        reply_markup=products_keyboard(products, category)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery):
    """Показать детальную информацию о товаре"""
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    product_id, name, description, price, category, file_path, content, is_active, created_at = product
    
    text = (
        f"📦 <b>{name}</b>\n\n"
        f"📝 {description}\n\n"
        f"💰 Цена: {price}₽\n"
        f"📂 Категория: {category}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=product_detail_keyboard(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    product_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id
    
    # Проверяем, есть ли уже такой товар в корзине
    existing_item = await db.get_cart_item(user_id, product_id)
    
    if existing_item:
        # Увеличиваем количество
        await db.update_cart_quantity(user_id, product_id, existing_item[3] + 1)
        await callback.answer("Количество товара увеличено!", show_alert=True)
    else:
        # Добавляем новый товар в корзину
        await db.add_to_cart(user_id, product_id, 1)
        await callback.answer("Товар добавлен в корзину!", show_alert=True)
    
    # Показываем обновленную информацию о товаре
    product = await db.get_product(product_id)
    if product:
        product_id, name, description, price, category, file_path, content, is_active, created_at = product
        
        text = (
            f"📦 <b>{name}</b>\n\n"
            f"📝 {description}\n\n"
            f"💰 Цена: {price}₽\n"
            f"📂 Категория: {category}\n\n"
            f"✅ Товар добавлен в корзину!"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=product_detail_keyboard(product_id),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Вернуться к списку категорий"""
    categories = await db.get_categories()
    if not categories:
        await callback.message.edit_text("Каталог пуст. Загляните позже!")
        return
    
    await callback.message.edit_text(
        "🛍 Выберите категорию товаров:",
        reply_markup=catalog_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показать содержимое корзины"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        cart_item_id, product_id, quantity = item[0], item[1], item[2]
        product = await db.get_product(product_id)
        
        if product:
            product_id, name, description, price, category, file_path, content, is_active, created_at = product
            item_total = price * quantity
            total_price += item_total
            cart_text += f"📦 {name} x{quantity} = {item_total}₽\n"
    
    cart_text += f"\n💰 <b>Итого: {total_price}₽</b>"
    
    # Создаем клавиатуру для корзины
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        cart_item_id, product_id, quantity = item[0], item[1], item[2]
        builder.button(
            text=f"❌ Удалить товар #{product_id}",
            callback_data=f"remove_from_cart:{cart_item_id}"
        )
    
    builder.button(
        text="💳 Оплатить",
        callback_data="checkout"
    )
    builder.button(
        text="🔙 В меню",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    
    await message.answer(
        cart_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: CallbackQuery):
    """Удалить товар из корзины"""
    cart_item_id = int(callback.data.split(":", 1)[1])
    await db.remove_from_cart(cart_item_id)
    
    await callback.answer("Товар удален из корзины", show_alert=True)
    
    # Показываем обновленную корзину
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text("🛒 Ваша корзина пуста!")
        return
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        cart_item_id, product_id, quantity = item[0], item[1], item[2]
        product = await db.get_product(product_id)
        
        if product:
            product_id, name, description, price, category, file_path, content, is_active, created_at = product
            item_total = price * quantity
            total_price += item_total
            cart_text += f"📦 {name} x{quantity} = {item_total}₽\n"
    
    cart_text += f"\n💰 <b>Итого: {total_price}₽</b>"
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        cart_item_id, product_id, quantity = item[0], item[1], item[2]
        builder.button(
            text=f"❌ Удалить товар #{product_id}",
            callback_data=f"remove_from_cart:{cart_item_id}"
        )
    
    builder.button(
        text="💳 Оплатить",
        callback_data="checkout"
    )
    builder.button(
        text="🔙 В меню",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
