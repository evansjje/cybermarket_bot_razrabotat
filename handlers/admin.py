# handlers/admin.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import settings
from database import (
    get_all_users_count,
    get_all_orders_count,
    get_all_orders,
    add_product,
    get_categories,
    get_products_by_category,
    delete_product,
    get_product
)
from keyboards import main_menu_kb

router = Router()


class AddProductForm(StatesGroup):
    """Форма добавления товара"""
    category_id = State()
    title = State()
    desc = State()
    price = State()
    file_data = State()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in settings.ADMIN_IDS


@router.message(F.text == "⚡ Админ-панель")
@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    """Главная админ-панель"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔️ У вас нет прав доступа к админ-панели.")
        return

    users_count = await get_all_users_count()
    orders_count = await get_all_orders_count()

    text = (
        f"⚡ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n\n"
        f"Выберите действие:"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Добавить товар", callback_data="admin_add_product")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
            [InlineKeyboardButton(text="📋 Список заказов", callback_data="admin_orders")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
        ]
    )

    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    categories = await get_categories()
    if not categories:
        await callback.message.answer("❌ Сначала добавьте категории в базу данных.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat[1], callback_data=f"admin_cat_{cat[0]}")]
            for cat in categories
        ] + [[InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_cancel")]]
    )

    await callback.message.answer("📂 Выберите категорию для товара:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_"))
async def admin_select_category(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор категории для нового товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    category_id = int(callback.data.split("_")[2])
    await state.set_state(AddProductForm.category_id)
    await state.update_data(category_id=category_id)

    await callback.message.answer("✏️ Введите название товара:")
    await callback.answer()


@router.message(AddProductForm.category_id)
async def admin_product_title(message: Message, state: FSMContext) -> None:
    """Ввод названия товара"""
    if not is_admin(message.from_user.id):
        await state.clear()
        await message.answer("⛔️ Нет доступа")
        return

    await state.update_data(title=message.text)
    await state.set_state(AddProductForm.title)
    await message.answer("📝 Введите описание товара:")


@router.message(AddProductForm.title)
async def admin_product_desc(message: Message, state: FSMContext) -> None:
    """Ввод описания товара"""
    if not is_admin(message.from_user.id):
        await state.clear()
        await message.answer("⛔️ Нет доступа")
        return

    await state.update_data(desc=message.text)
    await state.set_state(AddProductForm.desc)
    await message.answer("💰 Введите цену товара (число):")


@router.message(AddProductForm.desc)
async def admin_product_price(message: Message, state: FSMContext) -> None:
    """Ввод цены товара"""
    if not is_admin(message.from_user.id):
        await state.clear()
        await message.answer("⛔️ Нет доступа")
        return

    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0:")
        return

    await state.update_data(price=price)
    await state.set_state(AddProductForm.price)
    await message.answer("🔗 Введите ссылку на файл (или отправьте '-' если нет):")


@router.message(AddProductForm.price)
async def admin_product_file(message: Message, state: FSMContext) -> None:
    """Ввод ссылки на файл"""
    if not is_admin(message.from_user.id):
        await state.clear()
        await message.answer("⛔️ Нет доступа")
        return

    file_data = message.text if message.text != "-" else None
    await state.update_data(file_data=file_data)

    data = await state.get_data()
    category_id = data.get("category_id")
    title = data.get("title")
    desc = data.get("desc")
    price = data.get("price")

    await add_product(
        category_id=category_id,
        title=title,
        desc=desc,
        price=price,
        file_data=file_data
    )

    await state.clear()
    await message.answer(
        f"✅ Товар <b>{title}</b> успешно добавлен!\n"
        f"💰 Цена: {price} ₽",
        reply_markup=main_menu_kb(message.from_user.id)
    )


@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product_start(callback: CallbackQuery) -> None:
    """Начало удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    categories = await get_categories()
    if not categories:
        await callback.message.answer("❌ Нет категорий в базе.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat[1], callback_data=f"admin_del_cat_{cat[0]}")]
            for cat in categories
        ] + [[InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_cancel")]]
    )

    await callback.message.answer("📂 Выберите категорию для удаления товара:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_cat_"))
async def admin_delete_category_products(callback: CallbackQuery) -> None:
    """Выбор товара для удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    category_id = int(callback.data.split("_")[3])
    products = await get_products_by_category(category_id)

    if not products:
        await callback.message.answer("📭 В этой категории нет товаров.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{p[2]} — {p[4]} ₽", callback_data=f"admin_del_prod_{p[0]}")]
            for p in products
        ] + [[InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_cancel")]]
    )

    await callback.message.answer("📦 Выберите товар для удаления:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_prod_"))
async def admin_delete_product_confirm(callback: CallbackQuery) -> None:
    """Подтверждение удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    product_id = int(callback.data.split("_")[3])
    product = await get_product(product_id)

    if not product:
        await callback.message.answer("❌ Товар не найден.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_confirm_del_{product_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data="admin_cancel")
            ]
        ]
    )

    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить товар <b>{product[2]}</b>?",
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_confirm_del_"))
async def admin_delete_product_final(callback: CallbackQuery) -> None:
    """Финальное удаление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    product_id = int(callback.data.split("_")[3])
    product = await get_product(product_id)

    if not product:
        await callback.message.answer("❌ Товар не найден.")
        await callback.answer()
        return

    await delete_product(product_id)
    await callback.message.answer(f"✅ Товар <b>{product[2]}</b> удален.")
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery) -> None:
    """Просмотр всех заказов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    orders = await get_all_orders()

    if not orders:
        await callback.message.answer("📭 Заказов пока нет.")
        await callback.answer()
        return

    text = "📋 <b>Все заказы:</b>\n\n"
    for order in orders:
        # order: (id, user_id, product_id, count, created_at, title, price)
        order_id, user_id, product_id, count, created_at, title, price = order
        text += (
            f"🆔 Заказ #{order_id}\n"
            f"👤 Пользователь: {user_id}\n"
            f"📦 Товар: {title}\n"
            f"🔢 Кол-во: {count}\n"
            f"💰 Сумма: {price * count} ₽\n"
            f"🕐 Дата: {created_at}\n"
            f"─────────────\n"
        )

    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery) -> None:
    """Просмотр статистики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    users_count = await get_all_users_count()
    orders_count = await get_all_orders_count()

    text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: <b>{users_count}</b>\n"
        f"📦 Всего заказов: <b>{orders_count}</b>\n"
    )

    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена действия"""
    await state.clear()
    await callback.message.answer("❌ Действие отменено.")
    await callback.answer()
