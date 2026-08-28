# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from database import Database
from keyboards import (
    AdminCallback,
    CategoryCallback,
    ProductCallback,
    get_categories_keyboard,
    get_products_keyboard,
    get_main_menu
)
from config import settings

router = Router()


class AdminStates(StatesGroup):
    waiting_category_title = State()
    waiting_product_category = State()
    waiting_product_title = State()
    waiting_product_desc = State()
    waiting_product_price = State()
    waiting_edit_price = State()
    waiting_edit_desc = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message, db: Database):
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_stats()
    categories = await db.get_categories()

    text = (
        "⚡ <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"👥 Пользователей: {stats.get('users', 0)}\n"
        f"📦 Товаров: {stats.get('products', 0)}\n"
        f"🛒 Заказов в корзинах: {stats.get('cart_items', 0)}\n\n"
        f"📁 Категорий: {len(categories)}\n\n"
        "Выберите категорию для управления:"
    )

    keyboard = get_categories_keyboard(categories, user_id)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(AdminCallback.filter(F.action == 'add_category'))
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminStates.waiting_category_title)
    await callback.message.edit_text(
        "📝 Введите название новой категории:\n\n"
        "Или нажмите ❌ Отмена для выхода.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
            ]
        )
    )


@router.callback_query(AdminCallback.filter(F.action == 'delete_category'))
async def delete_category(callback: CallbackQuery, callback_data: AdminCallback, db: Database):
    await callback.answer()
    cat_id = callback_data.cat_id
    if cat_id:
        await db.delete_category(cat_id)
        await callback.answer("✅ Категория удалена!", show_alert=True)

    categories = await db.get_categories()
    user_id = callback.from_user.id
    try:
        await callback.message.edit_text(
            "⚡ <b>Админ-панель</b>\n\n"
            "Выберите категорию для управления:",
            reply_markup=get_categories_keyboard(categories, user_id)
        )
    except Exception:
        pass


@router.callback_query(AdminCallback.filter(F.action == 'add_product'))
async def add_product_category(callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
    await callback.answer()
    cat_id = callback_data.cat_id
    if not cat_id:
        await callback.answer("❌ Ошибка: категория не найдена", show_alert=True)
        return

    await state.update_data(product_category_id=cat_id)
    await state.set_state(AdminStates.waiting_product_title)
    await callback.message.edit_text(
        "📝 Введите название товара:\n\n"
        "Или нажмите ❌ Отмена для выхода.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
            ]
        )
    )


@router.callback_query(AdminCallback.filter(F.action == 'edit_product'))
async def edit_product(callback: CallbackQuery, callback_data: AdminCallback, db: Database):
    await callback.answer()
    product_id = callback_data.product_id
    if not product_id:
        await callback.answer("❌ Ошибка: товар не найден", show_alert=True)
        return

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Изменить цену",
                    callback_data=AdminCallback(action='edit_price', product_id=product_id).pack()
                ),
                InlineKeyboardButton(
                    text="📝 Изменить описание",
                    callback_data=AdminCallback(action='edit_desc', product_id=product_id).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить товар",
                    callback_data=AdminCallback(action='delete_product', product_id=product_id).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=AdminCallback(action='back_to_product', product_id=product_id).pack()
                )
            ]
        ]
    )

    text = (
        f"📦 <b>{product.get('title', 'Товар')}</b>\n\n"
        f"💰 Цена: {product.get('price', 0):.2f} ₽\n"
        f"📝 Описание: {product.get('desc', 'Нет описания')}\n\n"
        "Выберите действие:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(AdminCallback.filter(F.action == 'edit_price'))
async def edit_price_start(callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
    await callback.answer()
    product_id = callback_data.product_id
    if not product_id:
        await callback.answer("❌ Ошибка: товар не найден", show_alert=True)
        return

    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_price)
    await callback.message.edit_text(
        "💰 Введите новую цену товара:\n\n"
        "Или нажмите ❌ Отмена для выхода.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
            ]
        )
    )


@router.callback_query(AdminCallback.filter(F.action == 'edit_desc'))
async def edit_desc_start(callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
    await callback.answer()
    product_id = callback_data.product_id
    if not product_id:
        await callback.answer("❌ Ошибка: товар не найден", show_alert=True)
        return

    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_desc)
    await callback.message.edit_text(
        "📝 Введите новое описание товара:\n\n"
        "Или нажмите ❌ Отмена для выхода.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
            ]
        )
    )


@router.callback_query(AdminCallback.filter(F.action == 'delete_product'))
async def delete_product(callback: CallbackQuery, callback_data: AdminCallback, db: Database):
    await callback.answer()
    product_id = callback_data.product_id
    if product_id:
        await db.delete_product(product_id)
        await callback.answer("✅ Товар удален!", show_alert=True)

    # Возвращаемся к списку категорий
    categories = await db.get_categories()
    user_id = callback.from_user.id
    try:
        await callback.message.edit_text(
            "⚡ <b>Админ-панель</b>\n\n"
            "Выберите категорию для управления:",
            reply_markup=get_categories_keyboard(categories, user_id)
        )
    except Exception:
        pass


@router.callback_query(AdminCallback.filter(F.action == 'back_to_product'))
async def back_to_product(callback: CallbackQuery, callback_data: AdminCallback, db: Database):
    await callback.answer()
    product_id = callback_data.product_id
    if not product_id:
        await callback.answer("❌ Ошибка: товар не найден", show_alert=True)
        return

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    cat_id = product.get('category_id')
    products = await db.get_products(category_id=cat_id)
    user_id = callback.from_user.id

    try:
        await callback.message.edit_text(
            f"📦 Товары в категории:\n\nВыберите товар:",
            reply_markup=get_products_keyboard(products, cat_id, user_id)
        )
    except Exception:
        pass


@router.callback_query(F.data == 'admin_cancel')
async def admin_cancel(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    await state.clear()

    user_id = callback.from_user.id
    categories = await db.get_categories()

    try:
        await callback.message.edit_text(
            "⚡ <b>Админ-панель</b>\n\n"
            "Выберите категорию для управления:",
            reply_markup=get_categories_keyboard(categories, user_id)
        )
    except Exception:
        pass


@router.message(AdminStates.waiting_category_title)
async def process_category_title(message: Message, state: FSMContext, db: Database):
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return

    await db.add_category(title)
    await state.clear()

    user_id = message.from_user.id
    categories = await db.get_categories()

    await message.answer(
        f"✅ Категория «{title}» добавлена!",
        reply_markup=get_main_menu(user_id)
    )

    # Показываем обновленный список категорий
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите категорию для управления:",
        reply_markup=get_categories_keyboard(categories, user_id)
    )


@router.message(AdminStates.waiting_product_title)
async def process_product_title(message: Message, state: FSMContext, db: Database):
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return

    await state.update_data(product_title=title)
    await state.set_state(AdminStates.waiting_product_desc)
    await message.answer(
        "📝 Введите описание товара (или отправьте «-» для пустого описания):\n\n"
        "Или нажмите ❌ Отмена для выхода.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
            ]
        )
    )


@router.message(AdminStates.waiting_product_desc)
async def process_product_desc(message: Message, state: FSMContext, db: Database):
    desc = message.text.strip()
    if desc == '-':
        desc = ''

    await state.update_data(product_desc=desc)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        "💰 Введите цену товара (число):\n\n"
        "Или нажмите ❌ Отмена для выхода.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
            ]
        )
    )


@router.message(AdminStates.waiting_product_price)
async def process_product_price(message: Message, state: FSMContext, db: Database):
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0:")
        return

    data = await state.get_data()
    category_id = data.get('product_category_id')
    title = data.get('product_title')
    desc = data.get('product_desc', '')

    await db.add_product(category_id, title, desc, price)
    await state.clear()

    user_id = message.from_user.id
    categories = await db.get_categories()

    await message.answer(
        f"✅ Товар «{title}» добавлен!",
        reply_markup=get_main_menu(user_id)
    )

    # Показываем обновленный список категорий
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите категорию для управления:",
        reply_markup=get_categories_keyboard(categories, user_id)
    )


@router.message(AdminStates.waiting_edit_price)
async def process_edit_price(message: Message, state: FSMContext, db: Database):
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0:")
        return

    data = await state.get_data()
    product_id = data.get('edit_product_id')

    await db.update_product_price(product_id, price)
    await state.clear()

    user_id = message.from_user.id
    categories = await db.get_categories()

    await message.answer(
        "✅ Цена обновлена!",
        reply_markup=get_main_menu(user_id)
    )

    # Показываем обновленный список категорий
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите категорию для управления:",
        reply_markup=get_categories_keyboard(categories, user_id)
    )


@router.message(AdminStates.waiting_edit_desc)
async def process_edit_desc(message: Message, state: FSMContext, db: Database):
    desc = message.text.strip()
    if desc == '-':
        desc = ''

    data = await state.get_data()
    product_id = data.get('edit_product_id')

    await db.update_product_desc(product_id, desc)
    await state.clear()

    user_id = message.from_user.id
    categories = await db.get_categories()

    await message.answer(
        "✅ Описание обновлено!",
        reply_markup=get_main_menu(user_id)
    )

    # Показываем обновленный список категорий
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите категорию для управления:",
        reply_markup=get_categories_keyboard(categories, user_id)
    )
