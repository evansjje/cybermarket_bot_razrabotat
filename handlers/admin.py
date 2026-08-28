from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from database import (
    get_categories, get_products, get_product_by_id,
    delete_product, update_product_price, update_product_desc,
    get_stats, add_product
)
from keyboards import (
    admin_menu_kb, main_menu_kb, products_kb,
    admin_products_kb, admin_product_manage_kb
)
from config import settings

router = Router()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_product_title = State()
    waiting_for_product_price = State()
    waiting_for_product_desc = State()
    waiting_for_category = State()
    waiting_for_new_price = State()
    waiting_for_new_desc = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message):
    """Открытие админ-панели"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message):
    """Показ статистики"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    stats = await get_stats()
    await message.answer(
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📦 Заказов: <b>{stats['orders']}</b>\n"
        f"💰 Выручка: <b>{stats['revenue']}₽</b>",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '➕ Добавить товар')
async def add_product_start(message: Message, state: FSMContext):
    """Начало добавления товара"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    categories = await get_categories()
    if not categories:
        await message.answer("❌ Нет категорий для добавления товара.")
        return
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"📂 {cat['name']}",
                callback_data=f"add_cat_{cat['id']}"
            )] for cat in categories
        ]
    )
    
    await state.set_state(AdminStates.waiting_for_category)
    await message.answer(
        "📂 Выберите категорию для нового товара:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith('add_cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории для нового товара"""
    await callback.answer()
    category_id = int(callback.data.split('_')[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminStates.waiting_for_product_title)
    
    await callback.message.edit_text(
        "📝 Введите название товара:"
    )


@router.message(AdminStates.waiting_for_product_title)
async def add_product_title(message: Message, state: FSMContext):
    """Ввод названия товара"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Введите название:")
        return
    
    await state.update_data(title=title)
    await state.set_state(AdminStates.waiting_for_product_price)
    await message.answer(
        f"📦 Название: <b>{title}</b>\n\n"
        "💰 Введите цену товара (в рублях):"
    )


@router.message(AdminStates.waiting_for_product_price)
async def add_product_price(message: Message, state: FSMContext):
    """Ввод цены товара"""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    await state.update_data(price=price)
    await state.set_state(AdminStates.waiting_for_product_desc)
    await message.answer(
        f"💰 Цена: <b>{price}₽</b>\n\n"
        "📝 Введите описание товара (или отправьте '-' для пустого описания):"
    )


@router.message(AdminStates.waiting_for_product_desc)
async def add_product_desc(message: Message, state: FSMContext):
    """Ввод описания товара"""
    desc = message.text.strip()
    if desc == '-':
        desc = ''
    
    data = await state.get_data()
    
    try:
        await add_product(
            category_id=data['category_id'],
            title=data['title'],
            price=data['price'],
            description=desc
        )
        await state.clear()
        await message.answer(
            "✅ Товар успешно добавлен!",
            reply_markup=admin_menu_kb()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении товара: {e}",
            reply_markup=admin_menu_kb()
        )


@router.message(F.text == '📦 Управление товарами')
async def manage_products(message: Message):
    """Управление товарами"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    categories = await get_categories()
    if not categories:
        await message.answer("❌ Нет категорий с товарами.")
        return
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"📂 {cat['name']}",
                callback_data=f"admin_cat_{cat['id']}"
            )] for cat in categories
        ]
    )
    
    await message.answer(
        "📦 <b>Управление товарами</b>\n\n"
        "Выберите категорию:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith('admin_cat_'))
async def admin_category_products(callback: CallbackQuery):
    """Показ товаров категории для управления"""
    await callback.answer()
    category_id = int(callback.data.split('_')[2])
    kb = await admin_products_kb(category_id)
    
    await callback.message.edit_text(
        "📦 Товары в категории:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith('admin_prod_'))
async def admin_product_manage(callback: CallbackQuery):
    """Управление конкретным товаром"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return
    
    kb = await admin_product_manage_kb(product_id)
    
    text = (
        f"📦 <b>{product['title']}</b>\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>\n"
        f"📝 Описание: {product.get('description', 'Нет описания')}\n\n"
        f"Выберите действие:"
    )
    
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith('del_prod_'))
async def delete_product_handler(callback: CallbackQuery):
    """Удаление товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    
    try:
        await delete_product(product_id)
        await callback.message.edit_text(
            "✅ Товар успешно удален!",
            reply_markup=admin_menu_kb()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении товара: {e}",
            reply_markup=admin_menu_kb()
        )


@router.callback_query(F.data.startswith('edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало изменения цены"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_for_new_price)
    
    await callback.message.edit_text(
        "💰 Введите новую цену товара:"
    )


@router.message(AdminStates.waiting_for_new_price)
async def edit_price_finish(message: Message, state: FSMContext):
    """Завершение изменения цены"""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    data = await state.get_data()
    product_id = data['product_id']
    
    try:
        await update_product_price(product_id, price)
        await state.clear()
        await message.answer(
            "✅ Цена товара обновлена!",
            reply_markup=admin_menu_kb()
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при обновлении цены: {e}",
            reply_markup=admin_menu_kb()
        )


@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext):
    """Начало изменения описания"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_for_new_desc)
    
    await callback.message.edit_text(
        "📝 Введите новое описание товара (или отправьте '-' для пустого описания):"
    )


@router.message(AdminStates.waiting_for_new_desc)
async def edit_desc_finish(message: Message, state: FSMContext):
    """Завершение изменения описания"""
    desc = message.text.strip()
    if desc == '-':
        desc = ''
    
    data = await state.get_data()
    product_id = data['product_id']
    
    try:
        await update_product_desc(product_id, desc)
        await state.clear()
        await message.answer(
            "✅ Описание товара обновлено!",
            reply_markup=admin_menu_kb()
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при обновлении описания: {e}",
            reply_markup=admin_menu_kb()
        )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_kb(is_admin=is_admin)
    )


@router.callback_query(F.data == 'back_admin_categories')
async def back_to_admin_categories(callback: CallbackQuery):
    """Возврат к списку категорий в админке"""
    await callback.answer()
    categories = await get_categories()
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"📂 {cat['name']}",
                callback_data=f"admin_cat_{cat['id']}"
            )] for cat in categories
        ]
    )
    
    await callback.message.edit_text(
        "📦 <b>Управление товарами</b>\n\n"
        "Выберите категорию:",
        reply_markup=kb
    )
