from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from typing import List, Dict, Any, Optional
import logging

from config import Settings
from database import Database
from keyboards import (
    get_catalog_menu,
    get_products_menu,
    get_product_detail_menu,
    get_cart_menu,
    get_main_menu
)

logger = logging.getLogger(__name__)
settings = Settings()

router = Router()
db = Database(settings.DB_PATH)


class CartStates(StatesGroup):
    """Состояния для работы с корзиной."""
    viewing_cart = State()


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    """Показывает каталог с категориями."""
    try:
        categories = await db.get_categories()
        if not categories:
            categories = settings.DEFAULT_CATEGORIES
        await message.answer(
            "📁 Выберите категорию:",
            reply_markup=get_catalog_menu(categories)
        )
    except Exception as e:
        logger.error(f"Ошибка при показе каталога: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data.startswith("category:"))
async def show_products(callback: CallbackQuery):
    """Показывает товары в выбранной категории."""
    category = callback.data.split(":", 1)[1]
    try:
        products = await db.get_products_by_category(category)
        if not products:
            await callback.message.answer(
                f"📁 Категория «{category}» пуста.\n"
                "Товары скоро появятся!"
            )
        else:
            await callback.message.answer(
                f"📁 Категория: {category}\n"
                f"Найдено товаров: {len(products)}",
                reply_markup=get_products_menu(products, category)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при показе товаров: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery):
    """Показывает детальную информацию о товаре."""
    product_id = int(callback.data.split(":", 1)[1])
    try:
        product = await db.get_product(product_id)
        if not product:
            await callback.message.answer("❌ Товар не найден.")
            await callback.answer()
            return

        # Формируем описание товара
        description = product.get("description", "Описание отсутствует")
        price = product.get("price", 0)
        category = product.get("category", "Без категории")
        
        text = (
            f"📦 {product.get('name', 'Без названия')}\n\n"
            f"📝 {description}\n\n"
            f"📁 Категория: {category}\n"
            f"💰 Цена: {price} {settings.CURRENCY}\n"
        )
        
        # Если есть файл, показываем информацию о нем
        if product.get("file_path"):
            text += f"📎 Файл: {product['file_path'].split('/')[-1]}\n"
        
        await callback.message.answer(
            text,
            reply_markup=get_product_detail_menu(product_id, price)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при показе товара: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart(callback: CallbackQuery):
    """Добавляет товар в корзину."""
    product_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id
    
    try:
        # Проверяем существование товара
        product = await db.get_product(product_id)
        if not product:
            await callback.message.answer("❌ Товар не найден.")
            await callback.answer()
            return
        
        # Добавляем в корзину
        success = await db.add_to_cart(user_id, product_id)
        
        if success:
            await callback.message.answer(
                f"✅ Товар «{product['name']}» добавлен в корзину!\n\n"
                f"💰 Цена: {product['price']} {settings.CURRENCY}",
                reply_markup=get_cart_menu()
            )
        else:
            await callback.message.answer("❌ Не удалось добавить товар в корзину.")
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при добавлении в корзину: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показывает содержимое корзины."""
    user_id = message.from_user.id
    try:
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            await message.answer(
                "🛒 Ваша корзина пуста.\n"
                "Перейдите в каталог и добавьте товары!",
                reply_markup=get_main_menu()
            )
            return
        
        # Формируем текст корзины
        text = "🛒 Ваша корзина:\n\n"
        total = 0
        
        for item in cart_items:
            product = item.get("product", {})
            name = product.get("name", "Без названия")
            price = product.get("price", 0)
            quantity = item.get("quantity", 1)
            subtotal = price * quantity
            total += subtotal
            
            text += (
                f"📦 {name}\n"
                f"   Цена: {price} {settings.CURRENCY} × {quantity} = {subtotal} {settings.CURRENCY}\n\n"
            )
        
        text += f"💰 Итого: {total} {settings.CURRENCY}"
        
        await message.answer(
            text,
            reply_markup=get_cart_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при показе корзины: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очищает корзину."""
    user_id = callback.from_user.id
    try:
        await db.clear_cart(user_id)
        await callback.message.answer(
            "🗑 Корзина очищена.",
            reply_markup=get_main_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при очистке корзины: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Возвращает к каталогу."""
    try:
        categories = await db.get_categories()
        if not categories:
            categories = settings.DEFAULT_CATEGORIES
        await callback.message.answer(
            "📁 Выберите категорию:",
            reply_markup=get_catalog_menu(categories)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при возврате к каталогу: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возвращает в главное меню."""
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: CallbackQuery):
    """Удаляет товар из корзины."""
    product_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id
    
    try:
        await db.remove_from_cart(user_id, product_id)
        
        # Показываем обновленную корзину
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            await callback.message.answer(
                "🛒 Ваша корзина пуста.\n"
                "Перейдите в каталог и добавьте товары!",
                reply_markup=get_main_menu()
            )
        else:
            text = "🛒 Ваша корзина:\n\n"
            total = 0
            
            for item in cart_items:
                product = item.get("product", {})
                name = product.get("name", "Без названия")
                price = product.get("price", 0)
                quantity = item.get("quantity", 1)
                subtotal = price * quantity
                total += subtotal
                
                text += (
                    f"📦 {name}\n"
                    f"   Цена: {price} {settings.CURRENCY} × {quantity} = {subtotal} {settings.CURRENCY}\n\n"
                )
            
            text += f"💰 Итого: {total} {settings.CURRENCY}"
            
            await callback.message.answer(
                text,
                reply_markup=get_cart_menu()
            )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при удалении из корзины: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()


@router.callback_query(F.data.startswith("change_quantity:"))
async def change_quantity(callback: CallbackQuery):
    """Изменяет количество товара в корзине."""
    data = callback.data.split(":")
    product_id = int(data[1])
    action = data[2]  # "inc" или "dec"
    user_id = callback.from_user.id
    
    try:
        if action == "inc":
            await db.update_cart_quantity(user_id, product_id, 1)
        elif action == "dec":
            await db.update_cart_quantity(user_id, product_id, -1)
        
        # Показываем обновленную корзину
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            await callback.message.answer(
                "🛒 Ваша корзина пуста.\n"
                "Перейдите в каталог и добавьте товары!",
                reply_markup=get_main_menu()
            )
        else:
            text = "🛒 Ваша корзина:\n\n"
            total = 0
            
            for item in cart_items:
                product = item.get("product", {})
                name = product.get("name", "Без названия")
                price = product.get("price", 0)
                quantity = item.get("quantity", 1)
                subtotal = price * quantity
                total += subtotal
                
                text += (
                    f"📦 {name}\n"
                    f"   Цена: {price} {settings.CURRENCY} × {quantity} = {subtotal} {settings.CURRENCY}\n\n"
                )
            
            text += f"💰 Итого: {total} {settings.CURRENCY}"
            
            await callback.message.answer(
                text,
                reply_markup=get_cart_menu()
            )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при изменении количества: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()


@router.message(Command("cart"))
async def cart_command(message: Message):
    """Обработчик команды /cart."""
    await show_cart(message)


@router.message(Command("catalog"))
async def catalog_command(message: Message):
    """Обработчик команды /catalog."""
    await show_catalog(message)
