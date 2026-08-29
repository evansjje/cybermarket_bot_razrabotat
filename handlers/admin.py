from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import admin_menu, main_menu
from config import settings

router = Router()


class AdminStates(StatesGroup):
    waiting_category_name = State()
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()


@router.message(F.text == '⚡ Админ-панель')
async def admin_panel(message: Message, db: Database):
    """Показать админ-панель"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    await message.answer(
        "⚡ Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📊 Статистика')
async def show_statistics(message: Message, db: Database):
    """Показать статистику бота"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    users_count = await db.get_users_count()
    products_count = await db.get_products_count()
    orders_count = await db.get_orders_count()
    
    stats_text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📦 Товаров: {products_count}\n"
        f"🛒 Заказов: {orders_count}"
    )
    
    await message.answer(stats_text, reply_markup=admin_menu())


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext):
    """Начать добавление категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    await state.set_state(AdminStates.waiting_category_name)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='❌ Отмена', callback_data='cancel_add_category')
    
    await message.answer(
        "➕ Введите название новой категории:",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data == 'cancel_add_category')
async def cancel_add_category(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления категории"""
    await callback.answer()
    await state.clear()
    try:
        await callback.message.edit_text(
            "❌ Добавление категории отменено.",
            reply_markup=None
        )
    except Exception:
        pass
    await callback.message.answer("⚡ Админ-панель:", reply_markup=admin_menu())


@router.message(AdminStates.waiting_category_name)
async def process_category_name(message: Message, state: FSMContext, db: Database):
    """Обработка названия категории"""
    category_name = message.text.strip()
    
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым!")
        return
    
    try:
        await db.add_category(category_name)
        await state.clear()
        await message.answer(
            f"✅ Категория «{category_name}» успешно добавлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении категории: {str(e)}",
            reply_markup=admin_menu()
        )
        await state.clear()


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext):
    """Начать добавление товара"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    await state.set_state(AdminStates.waiting_product_name)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='❌ Отмена', callback_data='cancel_add_product')
    
    await message.answer(
        "➕ Введите название товара:",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data == 'cancel_add_product')
async def cancel_add_product(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления товара"""
    await callback.answer()
    await state.clear()
    try:
        await callback.message.edit_text(
            "❌ Добавление товара отменено.",
            reply_markup=None
        )
    except Exception:
        pass
    await callback.message.answer("⚡ Админ-панель:", reply_markup=admin_menu())


@router.message(AdminStates.waiting_product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка названия товара"""
    product_name = message.text.strip()
    
    if not product_name:
        await message.answer("❌ Название товара не может быть пустым!")
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='❌ Отмена', callback_data='cancel_add_product')
    
    await message.answer(
        "📝 Введите описание товара:",
        reply_markup=keyboard.as_markup()
    )


@router.message(AdminStates.waiting_product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка описания товара"""
    product_description = message.text.strip()
    
    if not product_description:
        await message.answer("❌ Описание товара не может быть пустым!")
        return
    
    await state.update_data(product_description=product_description)
    await state.set_state(AdminStates.waiting_product_price)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='❌ Отмена', callback_data='cancel_add_product')
    
    await message.answer(
        "💰 Введите цену товара (в рублях):",
        reply_markup=keyboard.as_markup()
    )


@router.message(AdminStates.waiting_product_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число)!")
        return
    
    await state.update_data(product_price=price)
    await state.set_state(AdminStates.waiting_product_category)
    
    # Показываем список категорий для выбора
    db = Database()
    await db.connect()
    categories = await db.get_categories()
    await db.close()
    
    if not categories:
        await message.answer(
            "❌ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        await state.clear()
        return
    
    keyboard = InlineKeyboardBuilder()
    for cat in categories:
        keyboard.button(
            text=cat['name'],
            callback_data=f'select_cat_{cat["id"]}'
        )
    keyboard.button(text='❌ Отмена', callback_data='cancel_add_product')
    keyboard.adjust(2)
    
    await message.answer(
        "📂 Выберите категорию для товара:",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('select_cat_'))
async def select_product_category(callback: CallbackQuery, state: FSMContext, db: Database):
    """Выбор категории для товара"""
    await callback.answer()
    
    category_id = int(callback.data.split('_')[2])
    data = await state.get_data()
    
    try:
        await db.add_product(
            category_id=category_id,
            name=data['product_name'],
            description=data['product_description'],
            price=data['product_price']
        )
        await state.clear()
        await callback.message.edit_text(
            f"✅ Товар «{data['product_name']}» успешно добавлен!",
            reply_markup=None
        )
        await callback.message.answer("⚡ Админ-панель:", reply_markup=admin_menu())
    except Exception as e:
        await state.clear()
        await callback.message.edit_text(
            f"❌ Ошибка при добавлении товара: {str(e)}",
            reply_markup=None
        )
        await callback.message.answer("⚡ Админ-панель:", reply_markup=admin_menu())


@router.message(F.text == '📦 Товары')
async def show_all_products(message: Message, db: Database):
    """Показать все товары для управления"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    products = await db.get_all_products()
    
    if not products:
        await message.answer(
            "📦 В базе пока нет товаров.",
            reply_markup=admin_menu()
        )
        return
    
    keyboard = InlineKeyboardBuilder()
    for product in products:
        keyboard.button(
            text=f"🗑 {product['name']} ({product['price']} ₽)",
            callback_data=f'delete_prod_{product["id"]}'
        )
    keyboard.adjust(1)
    
    await message.answer(
        "📦 <b>Все товары:</b>\n\n"
        "Нажмите на товар, чтобы удалить его:",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('delete_prod_'))
async def delete_product(callback: CallbackQuery, db: Database):
    """Удаление товара"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return
    
    try:
        await db.delete_product(product_id)
        await callback.message.edit_text(
            f"✅ Товар «{product['name']}» удален!",
            reply_markup=None
        )
        await callback.message.answer("⚡ Админ-панель:", reply_markup=admin_menu())
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении товара: {str(e)}",
            reply_markup=None
        )
        await callback.message.answer("⚡ Админ-панель:", reply_markup=admin_menu())


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu(is_admin)
    )
