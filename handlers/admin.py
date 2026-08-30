# handlers/admin.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm import State, FSMContext
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from contextlib import suppress
from database import Database
from keyboards import get_admin_menu, get_main_menu
from config import settings

router = Router()
db = Database()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_category_name = State()
    waiting_product_category = State()
    waiting_product_title = State()
    waiting_product_desc = State()
    waiting_product_price = State()
    waiting_new_price = State()
    waiting_new_desc = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: types.Message):
    """Открытие админ-панели"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "⚡ Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: types.Message):
    """Показ статистики"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_stats()
    if not stats:
        await message.answer("❌ Не удалось получить статистику.")
        return

    text = (
        "📊 Статистика магазина:\n\n"
        f"📁 Категорий: {stats.get('categories', 0)}\n"
        f"📦 Товаров: {stats.get('products', 0)}\n"
        f"🛒 Покупок: {stats.get('purchases', 0)}\n"
        f"👥 Пользователей: {stats.get('users', 0)}"
    )

    await message.answer(text, reply_markup=get_admin_menu())


@router.message(F.text == '➕ Категория')
async def add_category_start(message: types.Message, state: FSMContext):
    """Начало добавления категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await state.set_state(AdminStates.waiting_category_name)
    await message.answer(
        "📝 Введите название новой категории:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text='⬅️ Отмена')]],
            resize_keyboard=True
        )
    )


@router.message(AdminStates.waiting_category_name)
async def add_category_process(message: types.Message, state: FSMContext):
    """Обработка ввода названия категории"""
    if message.text == '⬅️ Отмена':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=get_admin_menu())
        return

    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
        return

    try:
        await db.add_category(category_name)
        await state.clear()
        await message.answer(
            f"✅ Категория «{category_name}» успешно добавлена!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при добавлении категории: {str(e)}",
            reply_markup=get_admin_menu()
        )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: types.Message, state: FSMContext):
    """Начало добавления товара"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "❌ Сначала добавьте хотя бы одну категорию!",
            reply_markup=get_admin_menu()
        )
        return

    # Создаем клавиатуру с категориями
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for cat in categories:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=cat.get('title', 'Категория'),
                callback_data=f"admin_prod_cat_{cat.get('id')}"
            )
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text='⬅️ Отмена', callback_data='admin_cancel')
    ])

    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        "📝 Выберите категорию для товара:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('admin_prod_cat_'))
async def add_product_category(callback: types.CallbackQuery, state: FSMContext):
    """Выбор категории для товара"""
    await callback.answer()

    try:
        category_id = int(callback.data.split('_')[-1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID категории.")
        return

    await state.update_data(product_category_id=category_id)
    await state.set_state(AdminStates.waiting_product_title)

    with suppress(Exception):
        await callback.message.edit_text(
            "📝 Введите название товара:",
            reply_markup=None
        )


@router.message(AdminStates.waiting_product_title)
async def add_product_title(message: types.Message, state: FSMContext):
    """Ввод названия товара"""
    if message.text == '⬅️ Отмена':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=get_admin_menu())
        return

    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
        return

    await state.update_data(product_title=title)
    await state.set_state(AdminStates.waiting_product_desc)
    await message.answer(
        "📝 Введите описание товара:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text='⬅️ Отмена')]],
            resize_keyboard=True
        )
    )


@router.message(AdminStates.waiting_product_desc)
async def add_product_desc(message: types.Message, state: FSMContext):
    """Ввод описания товара"""
    if message.text == '⬅️ Отмена':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=get_admin_menu())
        return

    desc = message.text.strip()
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте снова:")
        return

    await state.update_data(product_desc=desc)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        "💰 Введите цену товара (в рублях):",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text='⬅️ Отмена')]],
            resize_keyboard=True
        )
    )


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: types.Message, state: FSMContext):
    """Ввод цены товара"""
    if message.text == '⬅️ Отмена':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=get_admin_menu())
        return

    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError("Цена должна быть положительной")
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    category_id = data.get('product_category_id')
    title = data.get('product_title')
    desc = data.get('product_desc')

    try:
        await db.add_product(
            category_id=category_id,
            title=title,
            desc=desc,
            price=price
        )
        await state.clear()
        await message.answer(
            f"✅ Товар «{title}» успешно добавлен!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при добавлении товара: {str(e)}",
            reply_markup=get_admin_menu()
        )


@router.message(F.text == '📦 Товары')
async def show_products(message: types.Message):
    """Показ всех товаров для администрирования"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    products = await db.get_products()
    if not products:
        await message.answer(
            "📭 В магазине пока нет товаров.",
            reply_markup=get_admin_menu()
        )
        return

    # Создаем клавиатуру с товарами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for prod in products:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{prod.get('title')} — {prod.get('price')}₽",
                callback_data=f"admin_prod_{prod.get('id')}"
            )
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back')
    ])

    await message.answer(
        "📦 Список товаров:\n\n"
        "Нажмите на товар для управления:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('admin_prod_'))
async def admin_product_actions(callback: types.CallbackQuery):
    """Действия с товаром в админке"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[-1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID товара.")
        return

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.message.answer("❌ Товар не найден.")
        return

    # Клавиатура действий с товаром
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✏️ Цена', callback_data=f"admin_price_{product_id}"),
            InlineKeyboardButton(text='📝 Описание', callback_data=f"admin_desc_{product_id}")
        ],
        [
            InlineKeyboardButton(text='🗑 Удалить', callback_data=f"admin_delete_{product_id}")
        ],
        [
            InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back')
        ]
    ])

    text = (
        f"📦 Товар: {product.get('title')}\n"
        f"💰 Цена: {product.get('price')}₽\n"
        f"📝 Описание: {product.get('desc', 'Нет описания')}\n\n"
        f"Выберите действие:"
    )

    with suppress(Exception):
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == 'admin_back')
async def admin_back(callback: types.CallbackQuery):
    """Возврат к списку товаров"""
    await callback.answer()

    products = await db.get_products()
    if not products:
        with suppress(Exception):
            await callback.message.edit_text(
                "📭 В магазине пока нет товаров.",
                reply_markup=get_admin_menu()
            )
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for prod in products:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{prod.get('title')} — {prod.get('price')}₽",
                callback_data=f"admin_prod_{prod.get('id')}"
            )
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text='⬅️ Назад', callback_data='admin_back')
    ])

    with suppress(Exception):
        await callback.message.edit_text(
            "📦 Список товаров:\n\n"
            "Нажмите на товар для управления:",
            reply_markup=keyboard
        )


@router.callback_query(F.data == 'admin_cancel')
async def admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена действия"""
    await callback.answer()
    await state.clear()

    with suppress(Exception):
        await callback.message.edit_text(
            "❌ Действие отменено.",
            reply_markup=get_admin_menu()
        )


@router.callback_query(F.data.startswith('admin_price_'))
async def admin_change_price(callback: types.CallbackQuery, state: FSMContext):
    """Начало изменения цены"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[-1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID товара.")
        return

    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_new_price)

    with suppress(Exception):
        await callback.message.edit_text(
            "💰 Введите новую цену товара:",
            reply_markup=None
        )


@router.message(AdminStates.waiting_new_price)
async def admin_change_price_process(message: types.Message, state: FSMContext):
    """Обработка новой цены"""
    if message.text == '⬅️ Отмена':
        await state.clear()
        await message.answer("❌ Изменение отменено.", reply_markup=get_admin_menu())
        return

    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError("Цена должна быть положительной")
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    product_id = data.get('edit_product_id')

    try:
        await db.update_product_price(product_id, price)
        await state.clear()
        await message.answer(
            "✅ Цена товара успешно обновлена!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при обновлении цены: {str(e)}",
            reply_markup=get_admin_menu()
        )


@router.callback_query(F.data.startswith('admin_desc_'))
async def admin_change_desc(callback: types.CallbackQuery, state: FSMContext):
    """Начало изменения описания"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[-1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID товара.")
        return

    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_new_desc)

    with suppress(Exception):
        await callback.message.edit_text(
            "📝 Введите новое описание товара:",
            reply_markup=None
        )


@router.message(AdminStates.waiting_new_desc)
async def admin_change_desc_process(message: types.Message, state: FSMContext):
    """Обработка нового описания"""
    if message.text == '⬅️ Отмена':
        await state.clear()
        await message.answer("❌ Изменение отменено.", reply_markup=get_admin_menu())
        return

    desc = message.text.strip()
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте снова:")
        return

    data = await state.get_data()
    product_id = data.get('edit_product_id')

    try:
        await db.update_product_desc(product_id, desc)
        await state.clear()
        await message.answer(
            "✅ Описание товара успешно обновлено!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при обновлении описания: {str(e)}",
            reply_markup=get_admin_menu()
        )


@router.callback_query(F.data.startswith('admin_delete_'))
async def admin_delete_product(callback: types.CallbackQuery):
    """Удаление товара"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[-1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID товара.")
        return

    try:
        await db.delete_product(product_id)
        await callback.message.answer(
            "✅ Товар успешно удален!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка при удалении товара: {str(e)}",
            reply_markup=get_admin_menu()
        )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: types.Message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu(is_admin=is_admin)
    )
