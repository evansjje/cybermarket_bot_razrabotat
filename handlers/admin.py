from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import admin_menu, main_menu, products_keyboard, categories_keyboard
from config import settings

router = Router()


class CategoryStates(StatesGroup):
    waiting_for_title = State()


class ProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_desc = State()
    waiting_for_price = State()


class EditProductStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_desc = State()


@router.message(Command('admin'))
@router.message(F.text == '⚡ Админ-панель')
async def admin_panel(message: Message, state: FSMContext):
    """Открытие админ-панели"""
    await state.clear()
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
async def show_stats(message: Message):
    """Показ статистики бота"""
    user_id = message.from_user.id
    
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    stats = await db.get_stats()
    
    stats_text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"🛒 Заказов: <b>{stats['orders']}</b>\n"
        f"💰 Выручка: <b>{stats['revenue']}₽</b>"
    )
    
    await message.answer(stats_text)


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext):
    """Начало добавления категории"""
    user_id = message.from_user.id
    
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await state.set_state(CategoryStates.waiting_for_title)
    await message.answer(
        "📝 Введите название новой категории:\n\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(CategoryStates.waiting_for_title)
async def add_category_title(message: Message, state: FSMContext):
    """Получение названия категории"""
    title = message.text.strip()
    
    if len(title) < 2 or len(title) > 50:
        await message.answer("❌ Название должно быть от 2 до 50 символов. Попробуйте ещё раз:")
        return
    
    await db.add_category(title)
    await state.clear()
    
    await message.answer(
        f"✅ Категория «{title}» успешно добавлена!",
        reply_markup=admin_menu()
    )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext):
    """Начало добавления товара"""
    user_id = message.from_user.id
    
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    categories = await db.get_categories()
    
    if not categories:
        await message.answer(
            "❌ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        return
    
    await state.set_state(ProductStates.waiting_for_category)
    await message.answer(
        "📂 Выберите категорию для товара:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(ProductStates.waiting_for_category, F.data.startswith('cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории для товара"""
    await callback.answer()
    
    category_id = int(callback.data.split('_')[1])
    await state.update_data(category_id=category_id)
    await state.set_state(ProductStates.waiting_for_title)
    
    await callback.message.edit_text(
        "📝 Введите название товара:\n\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(ProductStates.waiting_for_title)
async def add_product_title(message: Message, state: FSMContext):
    """Получение названия товара"""
    title = message.text.strip()
    
    if len(title) < 2 or len(title) > 100:
        await message.answer("❌ Название должно быть от 2 до 100 символов. Попробуйте ещё раз:")
        return
    
    await state.update_data(title=title)
    await state.set_state(ProductStates.waiting_for_desc)
    
    await message.answer(
        "📝 Введите описание товара:\n\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(ProductStates.waiting_for_desc)
async def add_product_desc(message: Message, state: FSMContext):
    """Получение описания товара"""
    desc = message.text.strip()
    
    if len(desc) < 10 or len(desc) > 1000:
        await message.answer("❌ Описание должно быть от 10 до 1000 символов. Попробуйте ещё раз:")
        return
    
    await state.update_data(desc=desc)
    await state.set_state(ProductStates.waiting_for_price)
    
    await message.answer(
        "💰 Введите цену товара в рублях (число):\n\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(ProductStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    """Получение цены товара"""
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0. Попробуйте ещё раз:")
        return
    
    data = await state.get_data()
    
    await db.add_product(
        category_id=data['category_id'],
        title=data['title'],
        desc=data['desc'],
        price=price
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Товар «{data['title']}» успешно добавлен!",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📦 Товары')
async def show_all_products(message: Message):
    """Показ всех товаров для администрирования"""
    user_id = message.from_user.id
    
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    products = await db.get_products()
    
    if not products:
        await message.answer(
            "📭 Товаров пока нет. Добавьте их через ➕ Товар.",
            reply_markup=admin_menu()
        )
        return
    
    # Группируем товары по категориям
    categories = await db.get_categories()
    cat_map = {cat['id']: cat['title'] for cat in categories}
    
    text = "📦 <b>Все товары:</b>\n\n"
    
    for product in products:
        cat_title = cat_map.get(product['category_id'], 'Без категории')
        text += (
            f"🆔 {product['id']} | {cat_title}\n"
            f"📦 {product['title']}\n"
            f"💰 {product['price']}₽\n"
            f"➖➖➖➖➖➖➖\n"
        )
    
    # Создаем инлайн-кнопки для каждого товара
    buttons = []
    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {product['title']}",
                callback_data=f"admin_prod_{product['id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('admin_prod_'))
async def admin_product_actions(callback: CallbackQuery):
    """Действия с товаром в админке"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return
    
    text = (
        f"📦 <b>{product['title']}</b>\n\n"
        f"📝 {product['desc'] or 'Описание отсутствует'}\n\n"
        f"💰 Цена: {product['price']}₽\n"
        f"🆔 ID: {product['id']}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✏️ Цена', callback_data=f"edit_price_{product_id}"),
            InlineKeyboardButton(text='📝 Описание', callback_data=f"edit_desc_{product_id}")
        ],
        [
            InlineKeyboardButton(text='🗑 Удалить', callback_data=f"delete_prod_{product_id}")
        ],
        [
            InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products')
        ]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_products')
async def back_to_products(callback: CallbackQuery):
    """Возврат к списку товаров"""
    await callback.answer()
    
    products = await db.get_products()
    
    if not products:
        await callback.message.edit_text("📭 Товаров пока нет.")
        return
    
    categories = await db.get_categories()
    cat_map = {cat['id']: cat['title'] for cat in categories}
    
    text = "📦 <b>Все товары:</b>\n\n"
    
    for product in products:
        cat_title = cat_map.get(product['category_id'], 'Без категории')
        text += (
            f"🆔 {product['id']} | {cat_title}\n"
            f"📦 {product['title']}\n"
            f"💰 {product['price']}₽\n"
            f"➖➖➖➖➖➖➖\n"
        )
    
    buttons = []
    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {product['title']}",
                callback_data=f"admin_prod_{product['id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data.startswith('edit_price_'))
async def edit_product_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductStates.waiting_for_price)
    
    await callback.message.edit_text(
        "💰 Введите новую цену товара:\n\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(EditProductStates.waiting_for_price)
async def edit_product_price(message: Message, state: FSMContext):
    """Получение новой цены"""
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0. Попробуйте ещё раз:")
        return
    
    data = await state.get_data()
    product_id = data['product_id']
    
    await db.update_product_price(product_id, price)
    await state.clear()
    
    product = await db.get_product_by_id(product_id)
    
    await message.answer(
        f"✅ Цена товара «{product['title']}» обновлена до {price}₽!",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_product_desc_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductStates.waiting_for_desc)
    
    await callback.message.edit_text(
        "📝 Введите новое описание товара:\n\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(EditProductStates.waiting_for_desc)
async def edit_product_desc(message: Message, state: FSMContext):
    """Получение нового описания"""
    desc = message.text.strip()
    
    if len(desc) < 10 or len(desc) > 1000:
        await message.answer("❌ Описание должно быть от 10 до 1000 символов. Попробуйте ещё раз:")
        return
    
    data = await state.get_data()
    product_id = data['product_id']
    
    await db.update_product_desc(product_id, desc)
    await state.clear()
    
    product = await db.get_product_by_id(product_id)
    
    await message.answer(
        f"✅ Описание товара «{product['title']}» обновлено!",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data.startswith('delete_prod_'))
async def delete_product(callback: CallbackQuery):
    """Удаление товара"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return
    
    await db.delete_product(product_id)
    
    await callback.message.edit_text(
        f"🗑 Товар «{product['title']}» удалён!"
    )


@router.message(Command('cancel'))
async def cancel_command(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return
    
    await state.clear()
    
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin=is_admin)
    )
