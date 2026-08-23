from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from database import get_categories, get_products_by_category, get_product
from keyboards import categories_keyboard, products_keyboard, product_card_keyboard

router = Router()


@router.message(F.text == "🛍 Каталог")
async def show_categories(message: Message):
    """Показать категории товаров"""
    await message.answer(
        "📂 Выберите категорию товаров:",
        reply_markup=await categories_keyboard()
    )


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    """Показать товары выбранной категории"""
    category_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "🛍 Выберите товар:",
        reply_markup=await products_keyboard(category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product_card(callback: CallbackQuery):
    """Показать карточку товара"""
    product_id = int(callback.data.split("_")[1])
    product = await get_product(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    product_id, category_id, title, desc, price, file_data = product
    
    text = (
        f"📦 <b>{title}</b>\n\n"
        f"📝 {desc}\n\n"
        f"💰 Цена: <b>{price} ₽</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=await product_card_keyboard(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Вернуться к категориям"""
    await callback.message.edit_text(
        "📂 Выберите категорию товаров:",
        reply_markup=await categories_keyboard()
    )
    await callback.answer()
