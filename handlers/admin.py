# handlers/admin.py
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import main_menu_kb, admin_panel_kb, admin_products_kb
from config import settings

router = Router()
db = Database()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_stock = State()
    waiting_product_category = State()


def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    return user_id == settings.ADMIN_ID


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    # Получаем статистику
    users_count = await db.get_users_count()
    products_count = await db.get_products_count()
    orders_count = await db.get_orders_count()
    total_revenue = await db.get_total_revenue()

    stats_text = (
        "👨‍💻 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"🛍 Товаров: <b>{products_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n"
        f"💰 Выручка: <b>{total_revenue}₽</b>\n\n"
        "Выберите действие:"
    )

    await message.answer(
        stats_text,
        reply_markup=admin_panel_kb()
    )


@router.message(F.text == "👨‍💻 Админ-панель")
async def admin_panel_button(message: Message):
    """Открыть админ-панель через кнопку"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    # Получаем статистику
    users_count = await db.get_users_count()
    products_count = await db.get_products_count()
    orders_count = await db.get_orders_count()
    total_revenue = await db.get_total_revenue()

    stats_text = (
        "👨‍💻 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"🛍 Товаров: <b>{products_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n"
        f"💰 Выручка: <b>{total_revenue}₽</b>\n\n"
        "Выберите действие:"
    )

    await message.answer(
        stats_text,
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    users_count = await db.get_users_count()
    products_count = await db.get_products_count()
    orders_count = await db.get_orders_count()
    total_revenue = await db.get_total_revenue()

    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"🛍 Товаров: <b>{products_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n"
        f"💰 Выручка: <b>{total_revenue}₽</b>"
    )

    await callback.message.edit_text(
        stats_text,
        reply_markup=admin_panel_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_product_name)
    await callback.message.edit_text(
        "📝 <b>Добавление нового товара</b>\n\n"
        "Введите название товара:"
    )
    await callback.answer()


@router.message(AdminStates.waiting_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    """Получить название товара"""
    product_name = message.text.strip()

    if len(product_name) < 2 or len(product_name) > 100:
        await message.answer(
            "❌ Название должно быть от 2 до 100 символов.\n"
            "Попробуйте еще раз:"
        )
        return

    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)

    await message.answer(
        f"✅ Название: <b>{product_name}</b>\n\n"
        "Теперь введите описание товара:"
    )


@router.message(AdminStates.waiting_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    """Получить описание товара"""
    description = message.text.strip()

    if len(description) < 10 or len(description) > 1000:
        await message.answer(
            "❌ Описание должно быть от 10 до 1000 символов.\n"
            "Попробуйте еще раз:"
        )
        return

    await state.update_data(product_description=description)
    await state.set_state(AdminStates.waiting_product_price)

    await message.answer(
        "✅ Описание сохранено.\n\n"
        "Введите цену товара (в рублях):"
    )


@router.message(AdminStates.waiting_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получить цену товара"""
    try:
        price = float(message.text.replace(",", ".").replace(" ", ""))
        if price <= 0 or price > 1000000:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введите корректную цену (число больше 0 и меньше 1 000 000).\n"
            "Попробуйте еще раз:"
        )
        return

    await state.update_data(product_price=price)
    await state.set_state(AdminStates.waiting_product_stock)

    await message.answer(
        f"✅ Цена: <b>{price}₽</b>\n\n"
        "Введите количество товара на складе:"
    )


@router.message(AdminStates.waiting_product_stock)
async def admin_add_product_stock(message: Message, state: FSMContext):
    """Получить количество товара"""
    try:
        stock = int(message.text.strip())
        if stock < 0 or stock > 100000:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введите корректное количество (целое число от 0 до 100 000).\n"
            "Попробуйте еще раз:"
        )
        return

    await state.update_data(product_stock=stock)

    # Получаем категории для выбора
    categories = await db.get_categories()

    if not categories:
        await state.clear()
        await message.answer(
            "❌ Нет доступных категорий. Сначала создайте категорию."
        )
        return

    # Создаем клавиатуру с категориями
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 {cat['name']}",
                callback_data=f"admin_cat_{cat['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")])

    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        f"✅ Количество: <b>{stock}</b>\n\n"
        "Выберите категорию для товара:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(AdminStates.waiting_product_category, F.data.startswith("admin_cat_"))
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбрать категорию и сохранить товар"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    category_id = int(callback.data.split("_")[2])
    data = await state.get_data()

    product_name = data.get("product_name")
    product_description = data.get("product_description")
    product_price = data.get("product_price")
    product_stock = data.get("product_stock")

    # Добавляем товар в базу
    await db.add_product(
        category_id=category_id,
        name=product_name,
        description=product_description,
        price=product_price,
        stock=product_stock
    )

    await state.clear()

    await callback.message.edit_text(
        f"✅ <b>Товар успешно добавлен!</b>\n\n"
        f"📝 Название: <b>{product_name}</b>\n"
        f"📄 Описание: {product_description[:50]}...\n"
        f"💰 Цена: <b>{product_price}₽</b>\n"
        f"📦 Количество: <b>{product_stock}</b>\n"
        f"📁 Категория ID: <b>{category_id}</b>",
        reply_markup=admin_panel_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_products")
async def admin_products_list(callback: CallbackQuery):
    """Показать список товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    products = await db.get_all_products()

    if not products:
        await callback.message.edit_text(
            "📭 В базе нет товаров.",
            reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🛍 <b>Все товары ({len(products)}):</b>\n\n"
        "Выберите товар для просмотра:",
        reply_markup=admin_products_kb(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_prod_"))
async def admin_product_detail(callback: CallbackQuery):
    """Показать детали товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    product_id = int(callback.data.split("_")[2])
    product = await db.get_product(product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    category = await db.get_category(product['category_id'])
    category_name = category['name'] if category else "Без категории"

    product_text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"📄 {product['description']}\n\n"
        f"📁 Категория: <b>{category_name}</b>\n"
        f"💰 Цена: <b>{product['price']}₽</b>\n"
        f"📦 В наличии: <b>{product['stock']}</b>\n"
        f"🆔 ID: <b>{product['id']}</b>"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_products")],
        [InlineKeyboardButton(text="🏠 Админ-панель", callback_data="admin_stats")]
    ])

    await callback.message.edit_text(
        product_text,
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена действия"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено.",
        reply_markup=admin_panel_kb()
    )
    await callback.answer()


@router.message(F.text == "👨‍💻 Админ-панель")
async def admin_panel_text(message: Message):
    """Обработка текстовой кнопки админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    users_count = await db.get_users_count()
    products_count = await db.get_products_count()
    orders_count = await db.get_orders_count()
    total_revenue = await db.get_total_revenue()

    stats_text = (
        "👨‍💻 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"🛍 Товаров: <b>{products_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n"
        f"💰 Выручка: <b>{total_revenue}₽</b>\n\n"
        "Выберите действие:"
    )

    await message.answer(
        stats_text,
        reply_markup=admin_panel_kb()
    )
