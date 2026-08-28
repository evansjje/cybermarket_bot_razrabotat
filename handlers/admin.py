# handlers/admin.py
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm import State, FSMContext
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import admin_menu, main_menu, categories_keyboard, products_keyboard
from config import settings
from contextlib import suppress

router = Router()


class CategoryStates(StatesGroup):
    waiting_for_title = State()


class ProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()


class EditPriceStates(StatesGroup):
    waiting_for_price = State()


class EditDescStates(StatesGroup):
    waiting_for_desc = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message, db: Database) -> None:
    """Показ админ-панели."""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "⚡ Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message, db: Database) -> None:
    """Показ статистики."""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_stats()
    await message.answer(
        f"📊 <b>Статистика:</b>\n\n"
        f"👥 Пользователей: {stats.get('users', 0)}\n"
        f"📦 Товаров: {stats.get('products', 0)}\n"
        f"🗂 Категорий: {stats.get('categories', 0)}\n"
        f"🛒 Заказов: {stats.get('orders', 0)}"
    )


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext) -> None:
    """Начало добавления категории."""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await state.set_state(CategoryStates.waiting_for_title)
    await message.answer("📝 Введите название новой категории:")


@router.message(CategoryStates.waiting_for_title)
async def add_category_finish(message: Message, state: FSMContext, db: Database) -> None:
    """Завершение добавления категории."""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return

    await db.add_category(title)
    await state.clear()
    await message.answer(
        f"✅ Категория «{title}» добавлена!",
        reply_markup=admin_menu()
    )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database) -> None:
    """Начало добавления товара."""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    categories = await db.get_categories()
    if not categories:
        await message.answer("❌ Сначала добавьте хотя бы одну категорию!")
        return

    await state.set_state(ProductStates.waiting_for_category)
    await message.answer(
        "📝 Выберите категорию для товара:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(ProductStates.waiting_for_category, F.data.startswith('cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбор категории для нового товара."""
    await callback.answer()
    category_id = int(callback.data.split('_')[1])
    await state.update_data(category_id=category_id)
    await state.set_state(ProductStates.waiting_for_title)
    await callback.message.edit_text("📝 Введите название товара:")


@router.message(ProductStates.waiting_for_title)
async def add_product_title(message: Message, state: FSMContext) -> None:
    """Ввод названия товара."""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(title=title)
    await state.set_state(ProductStates.waiting_for_description)
    await message.answer("📝 Введите описание товара:")


@router.message(ProductStates.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext) -> None:
    """Ввод описания товара."""
    desc = message.text.strip()
    await state.update_data(desc=desc)
    await state.set_state(ProductStates.waiting_for_price)
    await message.answer("💰 Введите цену товара (в рублях):")


@router.message(ProductStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext, db: Database) -> None:
    """Ввод цены и завершение добавления товара."""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    category_id = data.get('category_id')
    title = data.get('title')
    desc = data.get('desc', '')

    await db.add_product(category_id, title, desc, price)
    await state.clear()
    await message.answer(
        f"✅ Товар «{title}» добавлен!",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📦 Товары')
async def show_products_admin(message: Message, db: Database) -> None:
    """Показ всех товаров для админа."""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    products = await db.get_products()
    if not products:
        await message.answer("📦 Товаров пока нет.")
        return

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product.get('title', 'Товар')} - {product.get('price', 0)}₽",
            callback_data=f"admin_prod_{product.get('id', 0)}"
        )
    builder.adjust(1)

    await message.answer(
        "📦 <b>Список товаров:</b>",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith('admin_prod_'))
async def admin_product_card(callback: CallbackQuery, db: Database) -> None:
    """Карточка товара для админа."""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)

    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return

    text = (
        f"📦 <b>{product.get('title', 'Товар')}</b>\n\n"
        f"💰 Цена: {product.get('price', 0)}₽\n"
        f"📝 Описание: {product.get('desc', 'Нет описания')}\n"
        f"🗂 Категория ID: {product.get('category_id', '?')}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Цена", callback_data=f"edit_price_{product_id}")
    builder.button(text="📝 Описание", callback_data=f"edit_desc_{product_id}")
    builder.button(text="🗑 Удалить", callback_data=f"delete_prod_{product_id}")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало редактирования цены."""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditPriceStates.waiting_for_price)
    await callback.message.edit_text("💰 Введите новую цену товара:")


@router.message(EditPriceStates.waiting_for_price)
async def edit_price_finish(message: Message, state: FSMContext, db: Database) -> None:
    """Завершение редактирования цены."""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    product_id = data.get('product_id')
    await db.update_product_price(product_id, price)
    await state.clear()
    await message.answer(
        "✅ Цена обновлена!",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало редактирования описания."""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditDescStates.waiting_for_desc)
    await callback.message.edit_text("📝 Введите новое описание товара:")


@router.message(EditDescStates.waiting_for_desc)
async def edit_desc_finish(message: Message, state: FSMContext, db: Database) -> None:
    """Завершение редактирования описания."""
    desc = message.text.strip()
    data = await state.get_data()
    product_id = data.get('product_id')
    await db.update_product_desc(product_id, desc)
    await state.clear()
    await message.answer(
        "✅ Описание обновлено!",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data.startswith('delete_prod_'))
async def delete_product(callback: CallbackQuery, db: Database) -> None:
    """Удаление товара."""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await db.delete_product(product_id)
    await callback.message.edit_text("🗑 Товар удалён!")


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database) -> None:
    """Возврат в главное меню."""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    await message.answer(
        "Вы вернулись в главное меню:",
        reply_markup=main_menu(is_admin=is_admin)
    )
