from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (
    get_all_users_count,
    get_all_orders_count,
    add_product,
    get_categories,
    get_products_by_category,
    get_product,
    delete_product,
    get_all_products
)
from keyboards import (
    main_menu_keyboard,
    admin_panel_keyboard,
    admin_products_keyboard,
    admin_product_actions_keyboard,
    admin_categories_keyboard
)
from config import settings

router = Router()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_product_title = State()
    waiting_product_desc = State()
    waiting_product_price = State()
    waiting_product_category = State()
    waiting_product_file = State()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in settings.ADMIN_IDS


@router.message(F.text == "⚡ Админ-панель")
@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Главная админ-панель"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("⛔️ У вас нет прав администратора!")
        return
    
    users_count = await get_all_users_count()
    orders_count = await get_all_orders_count()
    
    text = (
        f"⚡ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n\n"
        f"Выберите действие:"
    )
    
    await message.answer(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_product_title)
    await callback.message.edit_text(
        "📝 Введите название товара:",
        reply_markup=None
    )
    await callback.answer()


@router.message(AdminStates.waiting_product_title)
async def admin_add_product_title(message: Message, state: FSMContext):
    """Получение названия товара"""
    await state.update_data(title=message.text)
    await state.set_state(AdminStates.waiting_product_desc)
    await message.answer("📝 Введите описание товара:")


@router.message(AdminStates.waiting_product_desc)
async def admin_add_product_desc(message: Message, state: FSMContext):
    """Получение описания товара"""
    await state.update_data(desc=message.text)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer("💰 Введите цену товара (в рублях):")


@router.message(AdminStates.waiting_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получение цены товара"""
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    await state.update_data(price=price)
    await state.set_state(AdminStates.waiting_product_category)
    
    categories = await get_categories()
    if not categories:
        await message.answer("❌ Нет категорий. Сначала создайте категорию!")
        await state.clear()
        return
    
    await message.answer(
        "📂 Выберите категорию товара:",
        reply_markup=await admin_categories_keyboard(categories)
    )


@router.callback_query(AdminStates.waiting_product_category)
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    """Получение категории товара"""
    if not callback.data.startswith("admin_cat_"):
        await callback.answer("❌ Выберите категорию из списка!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminStates.waiting_product_file)
    
    await callback.message.edit_text(
        "📎 Отправьте файл товара (или введите 'skip' для пропуска):",
        reply_markup=None
    )
    await callback.answer()


@router.message(AdminStates.waiting_product_file)
async def admin_add_product_file(message: Message, state: FSMContext):
    """Получение файла товара"""
    data = await state.get_data()
    
    file_data = None
    if message.document:
        file_data = message.document.file_id
    elif message.text and message.text.lower() == "skip":
        file_data = None
    else:
        await message.answer("❌ Отправьте файл или введите 'skip':")
        return
    
    try:
        await add_product(
            category_id=data["category_id"],
            title=data["title"],
            desc=data["desc"],
            price=data["price"],
            file_data=file_data
        )
        
        await message.answer(
            f"✅ Товар <b>{data['title']}</b> успешно добавлен!",
            reply_markup=main_menu_keyboard(message.from_user.id),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении товара: {e}")
    
    await state.clear()


@router.callback_query(F.data == "admin_products")
async def admin_products_list(callback: CallbackQuery):
    """Список всех товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    
    products = await get_all_products()
    
    if not products:
        await callback.message.edit_text(
            "📦 Товаров пока нет.\n\n"
            "Добавьте первый товар через кнопку «➕ Добавить товар»",
            reply_markup=admin_panel_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📦 <b>Список товаров:</b>",
        reply_markup=await admin_products_keyboard(products),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_prod_"))
async def admin_product_detail(callback: CallbackQuery):
    """Детали товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    product = await get_product(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    product_id, category_id, title, desc, price, file_data = product
    
    text = (
        f"📦 <b>{title}</b>\n\n"
        f"📝 {desc}\n\n"
        f"💰 Цена: <b>{price} ₽</b>\n"
        f"📂 Категория ID: {category_id}\n"
        f"📎 Файл: {'✅' if file_data else '❌'}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=await admin_product_actions_keyboard(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_"))
async def admin_delete_product(callback: CallbackQuery):
    """Удаление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    
    try:
        await delete_product(product_id)
        await callback.answer("✅ Товар удален!", show_alert=True)
        
        # Обновляем список
        products = await get_all_products()
        if products:
            await callback.message.edit_text(
                "📦 <b>Список товаров:</b>",
                reply_markup=await admin_products_keyboard(products),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "📦 Товаров пока нет.\n\n"
                "Добавьте первый товар через кнопку «➕ Добавить товар»",
                reply_markup=admin_panel_keyboard()
            )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Возврат в админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    
    users_count = await get_all_users_count()
    orders_count = await get_all_orders_count()
    
    text = (
        f"⚡ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>\n\n"
        f"Выберите действие:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery):
    """Управление категориями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    
    categories = await get_categories()
    
    if not categories:
        await callback.message.edit_text(
            "📂 Категорий пока нет.",
            reply_markup=admin_panel_keyboard()
        )
        await callback.answer()
        return
    
    text = "📂 <b>Список категорий:</b>\n\n"
    for cat in categories:
        cat_id, cat_name = cat
        products = await get_products_by_category(cat_id)
        text += f"• {cat_name} — {len(products)} товаров\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
