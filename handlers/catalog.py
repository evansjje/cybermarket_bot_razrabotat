from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import catalog_kb, products_kb, product_detail_kb, main_menu_kb

router = Router()
db = Database()


class CartStates(StatesGroup):
    waiting_for_quantity = State()


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    categories = ["Скрипты", "Софт", "Мануалы"]
    await message.answer("Выберите категорию:", reply_markup=catalog_kb(categories))


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split("_", 1)[1]
    products = await db.get_products_by_category(category)
    if products:
        await callback.message.edit_text(f"Товары в категории '{category}':", reply_markup=products_kb(products, category))
    else:
        await callback.message.edit_text("В этой категории пока нет товаров.", reply_markup=catalog_kb(["Скрипты", "Софт", "Мануалы"]))
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    if product:
        text = f"📦 {product[1]}\n\n{product[2]}\n\n💰 Цена: {product[3]} руб."
        await callback.message.edit_text(text, reply_markup=product_detail_kb(product_id))
    else:
        await callback.message.edit_text("Товар не найден.")
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    # Проверяем, есть ли товар в корзине
    existing = await db.get_cart_item(user_id, product_id)
    if existing:
        await db.update_cart_quantity(user_id, product_id, existing[3] + 1)
    else:
        await db.add_to_cart(user_id, product_id, 1)
    
    await callback.answer("✅ Товар добавлен в корзину!")
    await callback.message.edit_text("Товар добавлен в корзину!", reply_markup=product_detail_kb(product_id))


@router.callback_query(F.data.startswith("back_"))
async def back_to_products(callback: CallbackQuery):
    category = callback.data.split("_", 1)[1]
    products = await db.get_products_by_category(category)
    await callback.message.edit_text(f"Товары в категории '{category}':", reply_markup=products_kb(products, category))
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb())
    await callback.answer()
