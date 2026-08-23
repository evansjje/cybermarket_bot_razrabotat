# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import get_categories, get_products_by_category, get_product
from keyboards import categories_kb, products_kb, product_card_kb

router = Router()


@router.message(F.text == "🛍 Каталог")
async def show_categories(message: Message) -> None:
    """Показать список категорий"""
    categories = await get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст. Загляните позже!")
        return

    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=categories_kb(categories)
    )


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery) -> None:
    """Показать товары выбранной категории"""
    category_id = int(callback.data.split("_")[1])
    products = await get_products_by_category(category_id)

    if not products:
        await callback.message.answer("📭 В этой категории пока нет товаров.")
        await callback.answer()
        return

    await callback.message.answer(
        "📦 Товары в категории:",
        reply_markup=products_kb(products, category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product_card(callback: CallbackQuery) -> None:
    """Показать карточку товара"""
    product_id = int(callback.data.split("_")[1])
    product = await get_product(product_id)

    if not product:
        await callback.message.answer("❌ Товар не найден.")
        await callback.answer()
        return

    # product: (id, category_id, title, desc, price, file_data)
    title = product[2]
    desc = product[3] or "Описание отсутствует"
    price = product[4]

    text = (
        f"📦 <b>{title}</b>\n\n"
        f"📝 {desc}\n\n"
        f"💰 Цена: <b>{price} ₽</b>"
    )

    await callback.message.answer(
        text,
        reply_markup=product_card_kb(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_cat_"))
async def back_to_categories(callback: CallbackQuery) -> None:
    """Вернуться к списку товаров категории"""
    category_id = int(callback.data.split("_")[2])
    products = await get_products_by_category(category_id)

    if not products:
        await callback.message.answer("📭 В этой категории пока нет товаров.")
        await callback.answer()
        return

    await callback.message.answer(
        "📦 Товары в категории:",
        reply_markup=products_kb(products, category_id)
    )
    await callback.answer()
