from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import admin_menu, main_menu, products_keyboard
from config import settings

router = Router()


class AdminStates(StatesGroup):
    waiting_category_name = State()
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()


@router.message(F.text == '⚡ Админ-панель')
async def admin_panel(message: Message, db: Database) -> None:
    """Показывает админ-панель"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await message.answer(
        "⚡ Админ-панель\nВыберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message, db: Database) -> None:
    """Показывает статистику бота"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа.")
        return
    
    stats = await db.get_stats()
    if not stats:
        await message.answer("❌ Не удалось получить статистику.")
        return
    
    text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: {stats.get('users_count', 0)}\n"
        f"📦 Товаров: {stats.get('products_count', 0)}\n"
        f"📁 Категорий: {stats.get('categories_count', 0)}\n"
        f"🛒 Заказов: {stats.get('orders_count', 0)}\n"
        f"💰 Общая выручка: {stats.get('total_revenue', 0)}₽"
    )
    await message.answer(text)


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext) -> None:
    """Начинает процесс добавления категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа.")
        return
    
    await state.set_state(AdminStates.waiting_category_name)
    await message.answer(
        "📝 Введите название новой категории:\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(AdminStates.waiting_category_name)
async def add_category_name(message: Message, state: FSMContext, db: Database) -> None:
    """Обрабатывает название категории"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление категории отменено.", reply_markup=admin_menu())
        return
    
    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    try:
        async with db.db.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (category_name,)
        ) as cursor:
            await db.db.commit()
        await state.clear()
        await message.answer(
            f"✅ Категория «{category_name}» успешно добавлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении категории: {str(e)}\n"
            "Возможно, такая категория уже существует. Попробуйте другое название:"
        )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database) -> None:
    """Начинает процесс добавления товара"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа.")
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "❌ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        return
    
    await state.set_state(AdminStates.waiting_product_name)
    await message.answer(
        "📝 Введите название товара:\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(AdminStates.waiting_product_name)
async def add_product_name(message: Message, state: FSMContext) -> None:
    """Обрабатывает название товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return
    
    product_name = message.text.strip()
    if not product_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer(
        "📝 Введите описание товара:\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(AdminStates.waiting_product_description)
async def add_product_description(message: Message, state: FSMContext) -> None:
    """Обрабатывает описание товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return
    
    description = message.text.strip()
    if not description:
        await message.answer("❌ Описание не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(product_description=description)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        "💰 Введите цену товара (число):\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: Message, state: FSMContext) -> None:
    """Обрабатывает цену товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return
    
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0. Попробуйте еще раз:")
        return
    
    await state.update_data(product_price=price)
    await state.set_state(AdminStates.waiting_product_category)
    
    categories = await db.get_categories()
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat['name'], callback_data=f'admin_cat_{cat["id"]}')
    builder.adjust(1)
    
    await message.answer(
        "📁 Выберите категорию для товара:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(AdminStates.waiting_product_category, F.data.startswith('admin_cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Обрабатывает выбор категории для товара"""
    await callback.answer()
    
    category_id = int(callback.data.split('_')[2])
    data = await state.get_data()
    
    try:
        async with db.db.execute(
            """
            INSERT INTO products (category_id, name, description, price)
            VALUES (?, ?, ?, ?)
            """,
            (category_id, data['product_name'], data['product_description'], data['product_price'])
        ) as cursor:
            await db.db.commit()
        
        await state.clear()
        await callback.message.edit_text(
            f"✅ Товар «{data['product_name']}» успешно добавлен!",
            reply_markup=None
        )
        await callback.message.answer(
            "Что дальше?",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await state.clear()
        await callback.message.edit_text(
            f"❌ Ошибка при добавлении товара: {str(e)}",
            reply_markup=None
        )
        await callback.message.answer(
            "Попробуйте снова.",
            reply_markup=admin_menu()
        )


@router.message(F.text == '📦 Товары')
async def show_products_admin(message: Message, db: Database) -> None:
    """Показывает список всех товаров для управления"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа.")
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer("📭 Каталог пуст.", reply_markup=admin_menu())
        return
    
    # Собираем все товары
    all_products = []
    for cat in categories:
        products = await db.get_products(cat['id'])
        for prod in products:
            prod['category_name'] = cat['name']
            all_products.append(prod)
    
    if not all_products:
        await message.answer("📭 В каталоге нет товаров.", reply_markup=admin_menu())
        return
    
    builder = InlineKeyboardBuilder()
    for prod in all_products:
        builder.button(
            text=f"🗑 {prod['name']} ({prod['category_name']})",
            callback_data=f'del_prod_{prod["id"]}'
        )
    builder.button(text='⬅️ Назад', callback_data='admin_back')
    builder.adjust(1)
    
    await message.answer(
        "📦 <b>Управление товарами:</b>\n"
        "Нажмите на товар, чтобы удалить его:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith('del_prod_'))
async def delete_product(callback: CallbackQuery, db: Database) -> None:
    """Удаляет товар"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return
    
    try:
        await db.delete_product(product_id)
        await callback.message.edit_text(
            f"✅ Товар «{product['name']}» удален!",
            reply_markup=None
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении: {str(e)}",
            reply_markup=None
        )


@router.callback_query(F.data == 'admin_back')
async def admin_back(callback: CallbackQuery) -> None:
    """Возвращает в админ-меню"""
    await callback.answer()
    await callback.message.edit_text(
        "⚡ Админ-панель\nВыберите действие:",
        reply_markup=None
    )
    await callback.message.answer(
        "⚡ Админ-панель",
        reply_markup=admin_menu()
    )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, state: FSMContext) -> None:
    """Возвращает в главное меню"""
    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(Command('cancel'))
async def cancel_command(message: Message, state: FSMContext) -> None:
    """Отменяет текущее действие"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return
    
    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    if is_admin:
        await message.answer("❌ Действие отменено.", reply_markup=admin_menu())
    else:
        await message.answer("❌ Действие отменено.", reply_markup=main_menu(is_admin=False))
