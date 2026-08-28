# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from contextlib import suppress

from database import Database
from keyboards import admin_menu, main_menu
from config import settings

router = Router()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_category_title = State()
    waiting_product_category = State()
    waiting_product_title = State()
    waiting_product_desc = State()
    waiting_product_price = State()
    waiting_new_price = State()
    waiting_new_desc = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id in settings.ADMIN_IDS


@router.message(F.text == '⚡ Админ-панель')
@router.message(F.text == '/admin')
async def admin_panel(message: Message, db: Database):
    """Открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "⚡ Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message, db: Database):
    """Показать статистику бота"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_stats()

    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats.get('users', 0)}</b>\n"
        f"📦 Товаров: <b>{stats.get('products', 0)}</b>\n"
        f"📁 Категорий: <b>{stats.get('categories', 0)}</b>\n"
        f"🛒 Товаров в корзинах: <b>{stats.get('cart_items', 0)}</b>\n"
    )

    await message.answer(text, reply_markup=admin_menu())


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext, db: Database):
    """Начать добавление категории"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await state.set_state(AdminStates.waiting_category_title)
    await message.answer(
        "📝 Введите название новой категории:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_category_title)
async def add_category_finish(message: Message, state: FSMContext, db: Database):
    """Завершить добавление категории"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    title = message.text.strip()
    if not title:
        await message.answer("⚠️ Название не может быть пустым. Попробуйте ещё раз:")
        return

    try:
        await db.add_category(title)
        await message.answer(
            f"✅ Категория <b>«{title}»</b> успешно добавлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении категории: {e}",
            reply_markup=admin_menu()
        )

    await state.clear()


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database):
    """Начать добавление товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "⚠️ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        return

    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(
            text=category.get('title', 'Категория'),
            callback_data=f"admin_add_prod_cat_{category.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back'))

    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        "📁 Выберите категорию для нового товара:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(AdminStates.waiting_product_category, F.data.startswith('admin_add_prod_cat_'))
async def add_product_category_selected(callback: CallbackQuery, state: FSMContext, db: Database):
    """Выбрана категория для товара"""
    await callback.answer()
    category_id = int(callback.data.split('_')[-1])

    await state.update_data(product_category_id=category_id)
    await state.set_state(AdminStates.waiting_product_title)

    await callback.message.edit_text(
        "📝 Введите название товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_product_title)
async def add_product_title(message: Message, state: FSMContext, db: Database):
    """Введено название товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    title = message.text.strip()
    if not title:
        await message.answer("⚠️ Название не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(product_title=title)
    await state.set_state(AdminStates.waiting_product_desc)

    await message.answer(
        "📝 Введите описание товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_product_desc)
async def add_product_desc(message: Message, state: FSMContext, db: Database):
    """Введено описание товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    desc = message.text.strip()
    await state.update_data(product_desc=desc)
    await state.set_state(AdminStates.waiting_product_price)

    await message.answer(
        "💰 Введите цену товара (в рублях):\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: Message, state: FSMContext, db: Database):
    """Введена цена товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    category_id = data.get('product_category_id')
    title = data.get('product_title')
    desc = data.get('product_desc', '')

    try:
        await db.add_product(category_id, title, desc, price)
        await message.answer(
            f"✅ Товар <b>«{title}»</b> успешно добавлен!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении товара: {e}",
            reply_markup=admin_menu()
        )

    await state.clear()


@router.message(F.text == '📦 Товары')
async def show_products_list(message: Message, db: Database):
    """Показать список всех товаров"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    products = await db.get_products()
    if not products:
        await message.answer(
            "📦 В базе пока нет товаров.",
            reply_markup=admin_menu()
        )
        return

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f"📦 {product.get('title', 'Товар')} — {product.get('price', 0):.2f} ₽",
            callback_data=f"admin_prod_{product.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back'))

    await message.answer(
        "📦 <b>Список всех товаров:</b>",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith('admin_prod_'))
async def show_product_admin(callback: CallbackQuery, db: Database):
    """Показать карточку товара для админа"""
    await callback.answer()
    product_id = int(callback.data.split('_')[-1])
    product = await db.get_product_by_id(product_id)

    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=admin_menu()
        )
        return

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✏️ Цена', callback_data=f"admin_edit_price_{product_id}"),
        InlineKeyboardButton(text='📝 Описание', callback_data=f"admin_edit_desc_{product_id}")
    )
    builder.row(InlineKeyboardButton(text='🗑 Удалить', callback_data=f"admin_delete_{product_id}"))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_products_back'))

    text = (
        f"📦 <b>{product.get('title', 'Товар')}</b>\n\n"
        f"💰 Цена: <b>{product.get('price', 0):.2f} ₽</b>\n"
        f"📝 Описание: {product.get('desc', 'Нет описания')}\n"
        f"🆔 ID: {product_id}"
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'admin_products_back')
async def admin_products_back(callback: CallbackQuery, db: Database):
    """Назад к списку товаров"""
    await callback.answer()
    products = await db.get_products()

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f"📦 {product.get('title', 'Товар')} — {product.get('price', 0):.2f} ₽",
            callback_data=f"admin_prod_{product.get('id')}"
        ))
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back'))

    with suppress(Exception):
        await callback.message.edit_text(
            "📦 <b>Список всех товаров:</b>",
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data.startswith('admin_edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начать изменение цены"""
    await callback.answer()
    product_id = int(callback.data.split('_')[-1])

    await state.set_state(AdminStates.waiting_new_price)
    await state.update_data(edit_product_id=product_id)

    await callback.message.edit_text(
        "💰 Введите новую цену товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_new_price)
async def edit_price_finish(message: Message, state: FSMContext, db: Database):
    """Завершить изменение цены"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Изменение отменено.", reply_markup=admin_menu())
        return

    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    product_id = data.get('edit_product_id')

    try:
        await db.update_product_price(product_id, price)
        await message.answer(
            f"✅ Цена товара обновлена до <b>{price:.2f} ₽</b>!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при обновлении цены: {e}",
            reply_markup=admin_menu()
        )

    await state.clear()


@router.callback_query(F.data.startswith('admin_edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начать изменение описания"""
    await callback.answer()
    product_id = int(callback.data.split('_')[-1])

    await state.set_state(AdminStates.waiting_new_desc)
    await state.update_data(edit_product_id=product_id)

    await callback.message.edit_text(
        "📝 Введите новое описание товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_new_desc)
async def edit_desc_finish(message: Message, state: FSMContext, db: Database):
    """Завершить изменение описания"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Изменение отменено.", reply_markup=admin_menu())
        return

    desc = message.text.strip()
    data = await state.get_data()
    product_id = data.get('edit_product_id')

    try:
        await db.update_product_desc(product_id, desc)
        await message.answer(
            "✅ Описание товара обновлено!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при обновлении описания: {e}",
            reply_markup=admin_menu()
        )

    await state.clear()


@router.callback_query(F.data.startswith('admin_delete_'))
async def delete_product(callback: CallbackQuery, db: Database):
    """Удалить товар"""
    await callback.answer()
    product_id = int(callback.data.split('_')[-1])

    try:
        await db.delete_product(product_id)
        await callback.message.edit_text(
            "✅ Товар успешно удалён!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении товара: {e}",
            reply_markup=admin_menu()
        )


@router.callback_query(F.data == 'admin_back')
async def admin_back(callback: CallbackQuery):
    """Назад в админ-меню"""
    await callback.answer()
    with suppress(Exception):
        await callback.message.edit_text(
            "⚡ Админ-панель\n\nВыберите действие:",
            reply_markup=admin_menu()
        )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database):
    """Назад в главное меню"""
    user_id = message.from_user.id
    is_admin_user = is_admin(user_id)
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=main_menu(is_admin=is_admin_user)
    )
