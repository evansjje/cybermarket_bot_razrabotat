from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database import Database
from keyboards import main_menu_kb, admin_menu_kb, categories_kb, products_kb, product_detail_kb, admin_products_kb, admin_product_detail_kb
from config import settings

router = Router()


class AdminStates(StatesGroup):
    """Состояния для FSM при работе с админкой"""
    waiting_for_category_title = State()
    waiting_for_product_category = State()
    waiting_for_product_title = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_edit_price = State()
    waiting_for_edit_desc = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message, db: Database):
    """Открытие админ-панели"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return
    
    await message.answer(
        "⚡ Админ-панель\nВыберите действие:",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message, db: Database):
    """Показ статистики"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return
    
    stats = await db.get_stats()
    await message.answer(
        f"📊 Статистика магазина:\n\n"
        f"👥 Пользователей: {stats.get('users', 0)}\n"
        f"🛒 Заказов: {stats.get('orders', 0)}\n"
        f"💰 Выручка: {stats.get('revenue', 0)}₽"
    )


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext, db: Database):
    """Начало добавления категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return
    
    await state.set_state(AdminStates.waiting_for_category_title)
    await message.answer("📝 Введите название новой категории:")


@router.message(AdminStates.waiting_for_category_title)
async def add_category_finish(message: Message, state: FSMContext, db: Database):
    """Завершение добавления категории"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return
    
    await db.add_category(title)
    await state.clear()
    await message.answer(
        f"✅ Категория «{title}» успешно добавлена!",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database):
    """Начало добавления товара"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "❌ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu_kb()
        )
        return
    
    await state.set_state(AdminStates.waiting_for_product_category)
    await message.answer(
        "📝 Выберите категорию для товара:",
        reply_markup=categories_kb(categories)
    )


@router.callback_query(AdminStates.waiting_for_product_category, F.data.startswith('cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext, db: Database):
    """Выбор категории для товара"""
    await callback.answer()
    
    category_id = int(callback.data.split('_')[1])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminStates.waiting_for_product_title)
    
    await callback.message.edit_text("📝 Введите название товара:")


@router.message(AdminStates.waiting_for_product_title)
async def add_product_title(message: Message, state: FSMContext, db: Database):
    """Ввод названия товара"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return
    
    await state.update_data(title=title)
    await state.set_state(AdminStates.waiting_for_product_description)
    await message.answer("📝 Введите описание товара:")


@router.message(AdminStates.waiting_for_product_description)
async def add_product_description(message: Message, state: FSMContext, db: Database):
    """Ввод описания товара"""
    desc = message.text.strip()
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте ещё раз:")
        return
    
    await state.update_data(desc=desc)
    await state.set_state(AdminStates.waiting_for_product_price)
    await message.answer("📝 Введите цену товара (в рублях):")


@router.message(AdminStates.waiting_for_product_price)
async def add_product_price(message: Message, state: FSMContext, db: Database):
    """Ввод цены товара"""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    data = await state.get_data()
    await db.add_product(
        category_id=data.get('category_id'),
        title=data.get('title'),
        desc=data.get('desc'),
        price=price
    )
    
    await state.clear()
    await message.answer(
        f"✅ Товар «{data.get('title')}» успешно добавлен!",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '📦 Товары')
async def show_all_products(message: Message, db: Database):
    """Показ всех товаров для админа"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return
    
    products = await db.get_products()
    if not products:
        await message.answer(
            "📭 В магазине пока нет товаров.",
            reply_markup=admin_menu_kb()
        )
        return
    
    await message.answer(
        "📦 Список всех товаров:",
        reply_markup=admin_products_kb(products)
    )


@router.callback_query(F.data.startswith('admin_prod_'))
async def admin_product_detail(callback: CallbackQuery, db: Database):
    """Детальный просмотр товара для админа"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден!")
        return
    
    await callback.message.edit_text(
        f"📦 Товар: {product.get('title')}\n"
        f"💰 Цена: {product.get('price')}₽\n"
        f"📝 Описание: {product.get('desc')}\n\n"
        f"Выберите действие:",
        reply_markup=admin_product_detail_kb(product_id)
    )


@router.callback_query(F.data.startswith('edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало редактирования цены"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_for_edit_price)
    
    await callback.message.edit_text("📝 Введите новую цену товара:")


@router.message(AdminStates.waiting_for_edit_price)
async def edit_price_finish(message: Message, state: FSMContext, db: Database):
    """Завершение редактирования цены"""
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
    
    product = await db.get_product_by_id(product_id)
    await message.answer(
        f"✅ Цена товара «{product.get('title')}» обновлена!\n"
        f"Новая цена: {price}₽",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало редактирования описания"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_for_edit_desc)
    
    await callback.message.edit_text("📝 Введите новое описание товара:")


@router.message(AdminStates.waiting_for_edit_desc)
async def edit_desc_finish(message: Message, state: FSMContext, db: Database):
    """Завершение редактирования описания"""
    desc = message.text.strip()
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте ещё раз:")
        return
    
    data = await state.get_data()
    product_id = data.get('product_id')
    
    await db.update_product_desc(product_id, desc)
    await state.clear()
    
    product = await db.get_product_by_id(product_id)
    await message.answer(
        f"✅ Описание товара «{product.get('title')}» обновлено!",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data.startswith('del_prod_'))
async def delete_product(callback: CallbackQuery, db: Database):
    """Удаление товара"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден!")
        return
    
    await db.delete_product(product_id)
    
    await callback.message.edit_text(
        f"✅ Товар «{product.get('title')}» удалён!",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "Вы вернулись в главное меню:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.callback_query(F.data == 'back_admin')
async def back_to_admin(callback: CallbackQuery, db: Database):
    """Возврат в админ-панель"""
    await callback.answer()
    
    await callback.message.edit_text(
        "⚡ Админ-панель\nВыберите действие:",
        reply_markup=admin_menu_kb()
    )
