# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import Database
from keyboards import admin_menu, main_menu, products_keyboard
from config import settings

router = Router()


class AdminStates(StatesGroup):
    """Состояния для FSM админ-панели"""
    waiting_category_name = State()
    waiting_product_category = State()
    waiting_product_title = State()
    waiting_product_desc = State()
    waiting_product_price = State()
    waiting_new_price = State()
    waiting_new_desc = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id in settings.ADMIN_IDS


@router.message(F.text == '⚡ Админ-панель')
@router.message(F.text == '/admin')
async def admin_panel(message: Message, db: Database):
    """Открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return

    await message.answer(
        "⚡ Админ-панель\n\nВыберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message, db: Database):
    """Показать статистику бота"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа!")
        return

    stats = await db.get_stats()
    
    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: {stats.get('users', 0)}\n"
        f"📦 Товаров: {stats.get('products', 0)}\n"
        f"🗂 Категорий: {stats.get('categories', 0)}\n"
        f"🛒 Покупок: {stats.get('purchases', 0)}\n"
        f"💰 Выручка: {stats.get('revenue', 0)}₽"
    )
    
    await message.answer(text)


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext):
    """Начать добавление категории"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа!")
        return

    await state.set_state(AdminStates.waiting_category_name)
    await message.answer(
        "📝 Введите название новой категории:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_category_name)
async def add_category_finish(message: Message, state: FSMContext, db: Database):
    """Завершить добавление категории"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=admin_menu())
        return

    category_title = message.text.strip()
    
    if not category_title:
        await message.answer("❌ Название не может быть пустым!")
        return

    try:
        await db.add_category(category_title)
        await state.clear()
        await message.answer(
            f"✅ Категория «{category_title}» успешно добавлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении категории: {str(e)}",
            reply_markup=admin_menu()
        )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database):
    """Начать добавление товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа!")
        return

    categories = await db.get_categories()
    
    if not categories:
        await message.answer(
            "❌ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=cat.get('title', 'Без названия'),
            callback_data=f"adm_cat_{cat.get('id', 0)}"
        )] for cat in categories
    ])

    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        "📝 Выберите категорию для товара:",
        reply_markup=keyboard
    )


@router.callback_query(AdminStates.waiting_product_category, F.data.startswith('adm_cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбрать категорию для товара"""
    await callback.answer()
    
    category_id = int(callback.data.split('_')[2])
    await state.update_data(product_category_id=category_id)
    await state.set_state(AdminStates.waiting_product_title)
    
    await callback.message.edit_text(
        "📝 Введите название товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_product_title)
async def add_product_title(message: Message, state: FSMContext):
    """Ввести название товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=admin_menu())
        return

    title = message.text.strip()
    
    if not title:
        await message.answer("❌ Название не может быть пустым!")
        return

    await state.update_data(product_title=title)
    await state.set_state(AdminStates.waiting_product_desc)
    await message.answer(
        "📝 Введите описание товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_product_desc)
async def add_product_desc(message: Message, state: FSMContext):
    """Ввести описание товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=admin_menu())
        return

    desc = message.text.strip()
    await state.update_data(product_desc=desc)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        "💰 Введите цену товара (в рублях):\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: Message, state: FSMContext, db: Database):
    """Ввести цену товара и сохранить"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=admin_menu())
        return

    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число)!")
        return

    data = await state.get_data()
    
    try:
        await db.add_product(
            category_id=data.get('product_category_id'),
            title=data.get('product_title'),
            desc=data.get('product_desc', ''),
            price=price
        )
        await state.clear()
        await message.answer(
            "✅ Товар успешно добавлен!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении товара: {str(e)}",
            reply_markup=admin_menu()
        )


@router.message(F.text == '📦 Товары')
async def show_all_products(message: Message, db: Database):
    """Показать все товары для администрирования"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа!")
        return

    products = await db.get_products()
    
    if not products:
        await message.answer(
            "📦 Товаров пока нет!",
            reply_markup=admin_menu()
        )
        return

    text = "📦 <b>Все товары:</b>\n\n"
    
    for prod in products:
        text += (
            f"🆔 {prod.get('id', 0)} | {prod.get('title', 'Без названия')}\n"
            f"💰 {prod.get('price', 0)}₽\n\n"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✏️ {prod.get('title', 'Без названия')}",
            callback_data=f"adm_prod_{prod.get('id', 0)}"
        )] for prod in products
    ])

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('adm_prod_'))
async def admin_product_actions(callback: CallbackQuery, db: Database):
    """Действия с товаром в админке"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден!")
        return

    text = (
        f"📦 <b>{product.get('title', 'Без названия')}</b>\n"
        f"💰 Цена: {product.get('price', 0)}₽\n"
        f"📝 Описание: {product.get('desc', 'Нет описания')}\n"
        f"🆔 ID: {product_id}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Цена",
                callback_data=f"adm_price_{product_id}"
            ),
            InlineKeyboardButton(
                text="📝 Описание",
                callback_data=f"adm_desc_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"adm_del_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="adm_back_products"
            )
        ]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data == 'adm_back_products')
async def admin_back_to_products(callback: CallbackQuery, db: Database):
    """Вернуться к списку товаров"""
    await callback.answer()
    
    products = await db.get_products()
    
    if not products:
        await callback.message.edit_text("📦 Товаров пока нет!")
        return

    text = "📦 <b>Все товары:</b>\n\n"
    
    for prod in products:
        text += (
            f"🆔 {prod.get('id', 0)} | {prod.get('title', 'Без названия')}\n"
            f"💰 {prod.get('price', 0)}₽\n\n"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✏️ {prod.get('title', 'Без названия')}",
            callback_data=f"adm_prod_{prod.get('id', 0)}"
        )] for prod in products
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data.startswith('adm_price_'))
async def edit_product_price_start(callback: CallbackQuery, state: FSMContext):
    """Начать изменение цены"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_new_price)
    
    await callback.message.edit_text(
        "💰 Введите новую цену товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_new_price)
async def edit_product_price_finish(message: Message, state: FSMContext, db: Database):
    """Завершить изменение цены"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Изменение отменено", reply_markup=admin_menu())
        return

    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число)!")
        return

    data = await state.get_data()
    product_id = data.get('edit_product_id')
    
    try:
        await db.update_product_price(product_id, price)
        await state.clear()
        await message.answer(
            "✅ Цена обновлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при обновлении цены: {str(e)}",
            reply_markup=admin_menu()
        )


@router.callback_query(F.data.startswith('adm_desc_'))
async def edit_product_desc_start(callback: CallbackQuery, state: FSMContext):
    """Начать изменение описания"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_new_desc)
    
    await callback.message.edit_text(
        "📝 Введите новое описание товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_new_desc)
async def edit_product_desc_finish(message: Message, state: FSMContext, db: Database):
    """Завершить изменение описания"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Изменение отменено", reply_markup=admin_menu())
        return

    desc = message.text.strip()
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    
    try:
        await db.update_product_desc(product_id, desc)
        await state.clear()
        await message.answer(
            "✅ Описание обновлено!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при обновлении описания: {str(e)}",
            reply_markup=admin_menu()
        )


@router.callback_query(F.data.startswith('adm_del_'))
async def delete_product(callback: CallbackQuery, db: Database):
    """Удалить товар"""
    await callback.answer()
    
    product_id = int(callback.data.split('_')[2])
    
    try:
        await db.delete_product(product_id)
        await callback.message.edit_text(
            "✅ Товар удален!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении товара: {str(e)}"
        )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database):
    """Вернуться в главное меню"""
    user_id = message.from_user.id
    is_admin_user = is_admin(user_id)
    
    await message.answer(
        "Вы вернулись в главное меню:",
        reply_markup=main_menu(is_admin_user)
    )
