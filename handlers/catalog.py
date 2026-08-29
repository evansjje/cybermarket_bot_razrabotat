from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from database import Database
from keyboards import categories_keyboard, products_keyboard, main_menu
from config import settings

router = Router()


@router.message(F.text == "🛍 Каталог")
async def show_categories(message: Message, state: FSMContext, db: Database):
    """Показать категории товаров"""
    await state.clear()
    
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("📭 Каталог пуст. Товары появятся позже.")
        return
    
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery, db: Database):
    """Показать товары выбранной категории"""
    await callback.answer()
    
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products(category_id=category_id)
    
    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=None
        )
        return
    
    # Получаем название категории для заголовка
    categories = await db.get_categories()
    category_title = next(
        (cat.get("title", "Категория") for cat in categories if cat.get("id") == category_id),
        "Категория"
    )
    
    await callback.message.edit_text(
        f"📂 {category_title}\n\nВыберите товар:",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith("prod_"))
async def show_product_details(callback: CallbackQuery, db: Database):
    """Показать карточку товара"""
    await callback.answer()
    
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=None
        )
        return
    
    from keyboards import product_card_keyboard
    
    product_text = (
        f"📦 <b>{product.get('title', 'Товар')}</b>\n\n"
        f"📝 {product.get('desc', 'Описание отсутствует')}\n\n"
        f"💰 Цена: <b>{product.get('price', 0):.2f} ₽</b>"
    )
    
    try:
        await callback.message.edit_text(
            product_text,
            reply_markup=product_card_keyboard(product_id),
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("buy_prod:"))
async def add_to_cart_callback(callback: CallbackQuery, db: Database):
    """Добавить товар в корзину"""
    await callback.answer()
    
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    try:
        await db.add_to_cart(user_id, product_id)
        await callback.answer("✅ Добавлено в корзину!", show_alert=False)
    except Exception:
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, db: Database):
    """Вернуться к списку категорий"""
    await callback.answer()
    
    categories = await db.get_categories()
    
    if not categories:
        await callback.message.edit_text(
            "📭 Каталог пуст.",
            reply_markup=None
        )
        return
    
    try:
        await callback.message.edit_text(
            "🛍 Выберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
    except Exception:
        pass
