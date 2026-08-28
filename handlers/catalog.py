from aiogram import Router, types, F
from aiogram.types import CallbackQuery, Message
from database import Database
from keyboards import categories_menu, products_menu, product_card, main_menu

router = Router()


@router.callback_query(F.data == "catalog")
async def show_categories(callback: CallbackQuery, db: Database) -> None:
    """Показать список категорий"""
    await callback.answer()
    categories = await db.get_categories()
    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=categories_menu(categories)
    )


@router.callback_query(F.data.startswith("category_"))
async def show_products(callback: CallbackQuery, db: Database) -> None:
    """Показать товары выбранной категории"""
    await callback.answer()
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products_by_category(category_id)
    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_menu(products, category_id)
    )


@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery, db: Database) -> None:
    """Показать карточку товара"""
    await callback.answer()
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return

    await callback.message.edit_text(
        f"📦 <b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>",
        reply_markup=product_card(product_id)
    )


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery, db: Database) -> None:
    """Добавить товар в корзину"""
    await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    product_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id

    # Проверяем, есть ли уже такой товар в корзине
    existing_item = await db.get_cart_item(user_id, product_id)
    if existing_item:
        await db.update_cart_item_count(user_id, product_id, existing_item['count'] + 1)
    else:
        await db.add_to_cart(user_id, product_id, 1)

    # Возвращаемся к карточке товара
    product = await db.get_product(product_id)
    if product:
        try:
            await callback.message.edit_text(
                f"📦 <b>{product['name']}</b>\n\n"
                f"{product['description']}\n\n"
                f"💰 Цена: <b>{product['price']}₽</b>",
                reply_markup=product_card(product_id)
            )
        except Exception:
            pass


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    """Вернуться в главное меню"""
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )
