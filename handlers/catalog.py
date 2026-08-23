import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database import Database
from keyboards import catalog_keyboard, product_keyboard, category_keyboard, main_menu_keyboard
from config import settings

logger = logging.getLogger(__name__)
router = Router()

# Состояния для добавления в корзину
class CartStates(StatesGroup):
    waiting_for_quantity = State()


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery, db: Database):
    """Показывает категории товаров"""
    categories = await db.get_categories()
    if not categories:
        await callback.message.edit_text(
            "📦 Каталог пуст. Загляните позже!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📦 Выберите категорию товаров:",
        reply_markup=category_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def show_products(callback: CallbackQuery, db: Database):
    """Показывает товары в выбранной категории"""
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products_by_category(category_id)
    
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🛍️ Товары в категории:",
        reply_markup=catalog_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product_details(callback: CallbackQuery, db: Database):
    """Показывает детальную информацию о товаре"""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Формируем описание товара
    description = f"""
<b>{product['name']}</b>

{product['description']}

💰 Цена: {product['price']} ₽
⭐ Рейтинг: {product.get('rating', 'Нет оценок')}
"""
    
    await callback.message.edit_text(
        description,
        reply_markup=product_keyboard(product_id, product['price']),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery, db: Database, state: FSMContext):
    """Добавление товара в корзину"""
    product_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    
    # Проверяем, есть ли товар в корзине
    existing_item = await db.get_cart_item(user_id, product_id)
    
    if existing_item:
        # Увеличиваем количество
        await db.update_cart_quantity(user_id, product_id, existing_item['quantity'] + 1)
        await callback.answer("✅ Количество товара увеличено!", show_alert=True)
    else:
        # Добавляем новый товар в корзину
        await db.add_to_cart(user_id, product_id, 1)
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    
    # Показываем корзину
    await show_cart(callback.message, db, user_id)


@router.callback_query(F.data == "view_cart")
async def show_cart(callback: CallbackQuery, db: Database):
    """Показывает содержимое корзины"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Формируем текст корзины
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total_price = 0
    
    for item in cart_items:
        product = item['product']
        subtotal = product['price'] * item['quantity']
        total_price += subtotal
        cart_text += f"• {product['name']} x{item['quantity']} = {subtotal} ₽\n"
    
    cart_text += f"\n💰 <b>Итого: {total_price} ₽</b>"
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=cart_keyboard(cart_items, total_price),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: CallbackQuery, db: Database):
    """Удаление товара из корзины"""
    product_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    
    await db.remove_from_cart(user_id, product_id)
    await callback.answer("🗑️ Товар удален из корзины")
    
    # Обновляем корзину
    await show_cart(callback, db)


@router.callback_query(F.data.startswith("change_quantity_"))
async def change_quantity(callback: CallbackQuery, db: Database, state: FSMContext):
    """Изменение количества товара в корзине"""
    parts = callback.data.split("_")
    product_id = int(parts[3])
    action = parts[4]  # 'inc' или 'dec'
    user_id = callback.from_user.id
    
    cart_item = await db.get_cart_item(user_id, product_id)
    if not cart_item:
        await callback.answer("Товар не найден в корзине", show_alert=True)
        return
    
    new_quantity = cart_item['quantity']
    if action == 'inc':
        new_quantity += 1
    elif action == 'dec':
        new_quantity -= 1
    
    if new_quantity <= 0:
        await db.remove_from_cart(user_id, product_id)
        await callback.answer("🗑️ Товар удален из корзины")
    else:
        await db.update_cart_quantity(user_id, product_id, new_quantity)
        await callback.answer("✅ Количество обновлено")
    
    # Обновляем корзину
    await show_cart(callback, db)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистка корзины"""
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    await callback.answer("🗑️ Корзина очищена")
    
    await callback.message.edit_text(
        "🛒 Ваша корзина пуста",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, db: Database):
    """Возврат к каталогу"""
    await show_catalog(callback, db)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, db: Database):
    """Возврат к категориям"""
    await show_catalog(callback, db)


# Вспомогательные функции
def cart_keyboard(cart_items: list, total_price: float):
    """Создает клавиатуру для корзины"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    for item in cart_items:
        product = item['product']
        # Кнопки для каждого товара
        buttons.append([
            InlineKeyboardButton(
                text=f"➖ {product['name']} ➕",
                callback_data=f"change_quantity_{product['id']}_inc"
            ),
            InlineKeyboardButton(
                text=f"Удалить {product['name']}",
                callback_data=f"remove_from_cart_{product['id']}"
            )
        ])
    
    # Кнопки управления
    buttons.append([
        InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart"),
        InlineKeyboardButton(text="💳 Оплатить", callback_data="checkout")
    ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="back_to_catalog")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Экспорт для использования в main.py
__all__ = ['router']
