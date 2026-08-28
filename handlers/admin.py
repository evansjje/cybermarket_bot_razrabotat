from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import main_menu
from config import settings

router = Router()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_category_name = State()
    waiting_category_description = State()
    waiting_product_category = State()
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()


def admin_menu() -> InlineKeyboardMarkup:
    """Инлайн-кнопки админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="➕ Добавить категорию", callback_data="admin_add_category")
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="🗑 Удалить товар", callback_data="admin_delete_product")
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def cancel_button() -> InlineKeyboardMarkup:
    """Кнопка отмены для FSM"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="admin_cancel")
    return builder.as_markup()


@router.message(F.text == "⚡ Админ-панель")
async def admin_panel(message: Message) -> None:
    """Показать админ-панель"""
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("⛔️ Доступ запрещен!")
        return
    
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, db: Database) -> None:
    """Показать статистику бота"""
    await callback.answer()
    
    try:
        users_count = await db.get_users_count()
        categories_count = await db.get_categories_count()
        products_count = await db.get_products_count()
        orders_count = await db.get_orders_count()
        
        stats_text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 Пользователей: <b>{users_count}</b>\n"
            f"📁 Категорий: <b>{categories_count}</b>\n"
            f"📦 Товаров: <b>{products_count}</b>\n"
            f"🛒 Заказов: <b>{orders_count}</b>"
        )
        
        await callback.message.edit_text(stats_text, reply_markup=admin_menu())
    except Exception:
        await callback.message.edit_text("❌ Ошибка получения статистики", reply_markup=admin_menu())


@router.callback_query(F.data == "admin_add_category")
async def admin_add_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать добавление категории"""
    await callback.answer()
    await state.set_state(AdminStates.waiting_category_name)
    
    try:
        await callback.message.edit_text(
            "➕ <b>Добавление новой категории</b>\n\n"
            "Введите название категории:",
            reply_markup=cancel_button()
        )
    except Exception:
        pass


@router.message(StateFilter(AdminStates.waiting_category_name))
async def admin_add_category_name(message: Message, state: FSMContext) -> None:
    """Получить название категории"""
    category_name = message.text.strip()
    
    if not category_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(category_name=category_name)
    await state.set_state(AdminStates.waiting_category_description)
    
    await message.answer(
        f"📝 Название: <b>{category_name}</b>\n\n"
        "Теперь введите описание категории:",
        reply_markup=cancel_button()
    )


@router.message(StateFilter(AdminStates.waiting_category_description))
async def admin_add_category_description(message: Message, state: FSMContext, db: Database) -> None:
    """Получить описание категории и сохранить"""
    category_description = message.text.strip()
    
    if not category_description:
        await message.answer("❌ Описание не может быть пустым. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    category_name = data.get('category_name')
    
    try:
        await db.add_category(category_name, category_description)
        await state.clear()
        await message.answer(
            f"✅ Категория <b>{category_name}</b> успешно добавлена!",
            reply_markup=main_menu()
        )
    except Exception:
        await state.clear()
        await message.answer(
            "❌ Ошибка при добавлении категории. Возможно, такая категория уже существует.",
            reply_markup=main_menu()
        )


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начать добавление товара"""
    await callback.answer()
    
    categories = await db.get_categories()
    if not categories:
        await callback.message.edit_text(
            "❌ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        return
    
    await state.set_state(AdminStates.waiting_product_category)
    
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category['name'],
            callback_data=f"admin_select_cat_{category['id']}"
        )
    builder.button(text="❌ Отмена", callback_data="admin_cancel")
    builder.adjust(1)
    
    try:
        await callback.message.edit_text(
            "➕ <b>Добавление нового товара</b>\n\n"
            "Выберите категорию:",
            reply_markup=builder.as_markup()
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_select_cat_"))
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбрать категорию для товара"""
    await callback.answer()
    
    category_id = int(callback.data.split("_")[3])
    await state.update_data(product_category_id=category_id)
    await state.set_state(AdminStates.waiting_product_name)
    
    try:
        await callback.message.edit_text(
            "📝 Введите название товара:",
            reply_markup=cancel_button()
        )
    except Exception:
        pass


@router.message(StateFilter(AdminStates.waiting_product_name))
async def admin_add_product_name(message: Message, state: FSMContext) -> None:
    """Получить название товара"""
    product_name = message.text.strip()
    
    if not product_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)
    
    await message.answer(
        f"📦 Название: <b>{product_name}</b>\n\n"
        "Теперь введите описание товара:",
        reply_markup=cancel_button()
    )


@router.message(StateFilter(AdminStates.waiting_product_description))
async def admin_add_product_description(message: Message, state: FSMContext) -> None:
    """Получить описание товара"""
    product_description = message.text.strip()
    
    if not product_description:
        await message.answer("❌ Описание не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(product_description=product_description)
    await state.set_state(AdminStates.waiting_product_price)
    
    await message.answer(
        f"📝 Описание: <b>{product_description}</b>\n\n"
        "Теперь введите цену товара (в рублях):",
        reply_markup=cancel_button()
    )


@router.message(StateFilter(AdminStates.waiting_product_price))
async def admin_add_product_price(message: Message, state: FSMContext, db: Database) -> None:
    """Получить цену товара и сохранить"""
    try:
        product_price = float(message.text.strip().replace(',', '.'))
        if product_price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    data = await state.get_data()
    
    try:
        await db.add_product(
            category_id=data['product_category_id'],
            name=data['product_name'],
            description=data['product_description'],
            price=product_price
        )
        await state.clear()
        await message.answer(
            f"✅ Товар <b>{data['product_name']}</b> успешно добавлен!",
            reply_markup=main_menu()
        )
    except Exception:
        await state.clear()
        await message.answer(
            "❌ Ошибка при добавлении товара.",
            reply_markup=main_menu()
        )


@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product_start(callback: CallbackQuery, db: Database) -> None:
    """Показать список товаров для удаления"""
    await callback.answer()
    
    products = await db.get_all_products()
    if not products:
        try:
            await callback.message.edit_text(
                "❌ В базе нет товаров для удаления.",
                reply_markup=admin_menu()
            )
        except Exception:
            pass
        return
    
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"🗑 {product['name']} - {product['price']}₽",
            callback_data=f"admin_del_prod_{product['id']}"
        )
    builder.button(text="❌ Отмена", callback_data="admin_cancel")
    builder.adjust(1)
    
    try:
        await callback.message.edit_text(
            "🗑 <b>Удаление товара</b>\n\n"
            "Выберите товар для удаления:",
            reply_markup=builder.as_markup()
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_del_prod_"))
async def admin_delete_product_confirm(callback: CallbackQuery, db: Database) -> None:
    """Подтверждение удаления товара"""
    await callback.answer()
    
    product_id = int(callback.data.split("_")[3])
    product = await db.get_product(product_id)
    
    if not product:
        try:
            await callback.message.edit_text(
                "❌ Товар не найден.",
                reply_markup=admin_menu()
            )
        except Exception:
            pass
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"admin_confirm_del_{product_id}")
    builder.button(text="❌ Отмена", callback_data="admin_cancel")
    builder.adjust(1)
    
    try:
        await callback.message.edit_text(
            f"⚠️ Вы уверены, что хотите удалить товар?\n\n"
            f"📦 <b>{product['name']}</b>\n"
            f"💰 Цена: {product['price']}₽",
            reply_markup=builder.as_markup()
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_confirm_del_"))
async def admin_delete_product_execute(callback: CallbackQuery, db: Database) -> None:
    """Выполнить удаление товара"""
    await callback.answer()
    
    product_id = int(callback.data.split("_")[3])
    
    try:
        await db.delete_product(product_id)
        await callback.message.edit_text(
            "✅ Товар успешно удален!",
            reply_markup=admin_menu()
        )
    except Exception:
        try:
            await callback.message.edit_text(
                "❌ Ошибка при удалении товара.",
                reply_markup=admin_menu()
            )
        except Exception:
            pass


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена операции"""
    await callback.answer()
    await state.clear()
    
    try:
        await callback.message.edit_text(
            "⚡ <b>Админ-панель</b>\n\n"
            "Выберите действие:",
            reply_markup=admin_menu()
        )
    except Exception:
        pass
