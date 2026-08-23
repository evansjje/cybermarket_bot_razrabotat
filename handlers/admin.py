from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import settings
from database import get_connection
from keyboards import get_main_menu

router = Router()


class ProductForm(StatesGroup):
    title = State()
    desc = State()
    price = State()
    category_id = State()
    file_data = State()


@router.message(F.text == "⚡ Админ-панель")
@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    """Админ-панель: статистика и управление"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ Доступ запрещен. Вы не администратор.")
        return

    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM users")
        users_count = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM orders")
        orders_count = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM products")
        products_count = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM categories")
        categories_count = (await cursor.fetchone())["cnt"]
    finally:
        await conn.close()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
            [InlineKeyboardButton(text="📦 Список товаров", callback_data="admin_list_products")],
            [InlineKeyboardButton(text="📂 Список категорий", callback_data="admin_list_categories")],
        ]
    )

    await message.answer(
        f"⚡ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📦 Товаров: {products_count}\n"
        f"📂 Категорий: {categories_count}\n"
        f"🛒 Заказов: {orders_count}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало добавления товара"""
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text("📝 Введите название товара:")
    await state.set_state(ProductForm.title)
    await callback.answer()


@router.message(ProductForm.title)
async def admin_add_product_title(message: Message, state: FSMContext) -> None:
    """Получение названия товара"""
    await state.update_data(title=message.text)
    await message.answer("📝 Введите описание товара:")
    await state.set_state(ProductForm.desc)


@router.message(ProductForm.desc)
async def admin_add_product_desc(message: Message, state: FSMContext) -> None:
    """Получение описания товара"""
    await state.update_data(desc=message.text)
    await message.answer("💰 Введите цену товара (число):")
    await state.set_state(ProductForm.price)


@router.message(ProductForm.price)
async def admin_add_product_price(message: Message, state: FSMContext) -> None:
    """Получение цены товара"""
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0:")
        return

    await state.update_data(price=price)

    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT id, name FROM categories ORDER BY id")
        categories = await cursor.fetchall()
    finally:
        await conn.close()

    if not categories:
        await message.answer("❌ Сначала создайте категорию в БД.")
        await state.clear()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat["name"], callback_data=f"admin_cat_{cat['id']}")]
            for cat in categories
        ]
    )
    await message.answer("📂 Выберите категорию:", reply_markup=keyboard)
    await state.set_state(ProductForm.category_id)


@router.callback_query(ProductForm.category_id, F.data.startswith("admin_cat_"))
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение категории товара"""
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    await callback.message.edit_text("📎 Отправьте файл товара (или отправьте '-' если файла нет):")
    await state.set_state(ProductForm.file_data)
    await callback.answer()


@router.message(ProductForm.file_data)
async def admin_add_product_file(message: Message, state: FSMContext) -> None:
    """Получение файла товара"""
    file_data = None
    if message.document:
        file_data = message.document.file_id
    elif message.text == "-":
        file_data = None
    else:
        await message.answer("❌ Отправьте файл или '-' для пропуска:")
        return

    await state.update_data(file_data=file_data)
    data = await state.get_data()

    conn = await get_connection()
    try:
        await conn.execute(
            """INSERT INTO products (category_id, title, desc, price, file_data)
               VALUES (?, ?, ?, ?, ?)""",
            (data["category_id"], data["title"], data["desc"], data["price"], data["file_data"])
        )
        await conn.commit()
    finally:
        await conn.close()

    await state.clear()
    await message.answer("✅ Товар успешно добавлен!")

    keyboard = await get_main_menu(message.from_user.id)
    await message.answer("Возвращаемся в меню:", reply_markup=keyboard)


@router.callback_query(F.data == "admin_list_products")
async def admin_list_products(callback: CallbackQuery) -> None:
    """Список всех товаров"""
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """SELECT p.id, p.title, p.price, c.name as category
               FROM products p
               JOIN categories c ON p.category_id = c.id
               ORDER BY p.id"""
        )
        products = await cursor.fetchall()
    finally:
        await conn.close()

    if not products:
        await callback.message.edit_text("📭 Товаров пока нет.")
        await callback.answer()
        return

    text = "📦 <b>Все товары:</b>\n\n"
    for product in products:
        text += f"#{product['id']} — {product['title']} ({product['category']}) — {product['price']}₽\n"

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "admin_list_categories")
async def admin_list_categories(callback: CallbackQuery) -> None:
    """Список всех категорий"""
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT id, name FROM categories ORDER BY id")
        categories = await cursor.fetchall()
    finally:
        await conn.close()

    if not categories:
        await callback.message.edit_text("📭 Категорий пока нет.")
        await callback.answer()
        return

    text = "📂 <b>Все категории:</b>\n\n"
    for category in categories:
        text += f"#{category['id']} — {category['name']}\n"

    await callback.message.edit_text(text)
    await callback.answer()
