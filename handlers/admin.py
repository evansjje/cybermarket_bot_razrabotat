from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart

from database import Database
from keyboards import admin_menu, main_menu, products_keyboard, categories_keyboard
from config import settings

router = Router()


class CategoryForm(StatesGroup):
    title = State()


class ProductForm(StatesGroup):
    category_id = State()
    title = State()
    desc = State()
    price = State()


class EditPriceForm(StatesGroup):
    price = State()


class EditDescForm(StatesGroup):
    desc = State()


@router.message(F.text == "⚡ Админ-панель")
@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext, db: Database):
    """Открыть админ-панель"""
    await state.clear()
    
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message, state: FSMContext, db: Database):
    """Показать статистику бота"""
    await state.clear()
    
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    stats = await db.get_stats()
    
    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats.get('users', 0)}</b>\n"
        f"📂 Категорий: <b>{stats.get('categories', 0)}</b>\n"
        f"📦 Товаров: <b>{stats.get('products', 0)}</b>\n"
        f"🛒 Заказов в корзинах: <b>{stats.get('cart_items', 0)}</b>",
        reply_markup=admin_menu()
    )


# ==================== КАТЕГОРИИ ====================

@router.message(F.text == "➕ Категория")
async def add_category_start(message: Message, state: FSMContext, db: Database):
    """Начать добавление категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await state.set_state(CategoryForm.title)
    await message.answer(
        "➕ <b>Добавление категории</b>\n\n"
        "Введите название категории:\n"
        "или /cancel для отмены"
    )


@router.message(CategoryForm.title)
async def add_category_title(message: Message, state: FSMContext, db: Database):
    """Получить название категории"""
    title = message.text.strip()
    
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return
    
    try:
        await db.add_category(title)
        await state.clear()
        await message.answer(
            f"✅ Категория <b>«{title}»</b> успешно добавлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении категории: {e}\n"
            f"Возможно, такая категория уже существует.",
            reply_markup=admin_menu()
        )
        await state.clear()


# ==================== ТОВАРЫ ====================

@router.message(F.text == "➕ Товар")
async def add_product_start(message: Message, state: FSMContext, db: Database):
    """Начать добавление товара"""
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
    
    await state.set_state(ProductForm.category_id)
    await message.answer(
        "➕ <b>Добавление товара</b>\n\n"
        "Выберите категорию:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(ProductForm.category_id, F.data.startswith("cat_"))
async def add_product_category(callback: CallbackQuery, state: FSMContext, db: Database):
    """Выбрать категорию для товара"""
    await callback.answer()
    
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(ProductForm.title)
    
    await callback.message.edit_text(
        "Введите название товара:\n"
        "или /cancel для отмены"
    )


@router.message(ProductForm.title)
async def add_product_title(message: Message, state: FSMContext, db: Database):
    """Получить название товара"""
    title = message.text.strip()
    
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return
    
    await state.update_data(title=title)
    await state.set_state(ProductForm.desc)
    await message.answer(
        "Введите описание товара:\n"
        "или /cancel для отмены"
    )


@router.message(ProductForm.desc)
async def add_product_desc(message: Message, state: FSMContext, db: Database):
    """Получить описание товара"""
    desc = message.text.strip()
    
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте ещё раз:")
        return
    
    await state.update_data(desc=desc)
    await state.set_state(ProductForm.price)
    await message.answer(
        "Введите цену товара (в рублях):\n"
        "или /cancel для отмены"
    )


@router.message(ProductForm.price)
async def add_product_price(message: Message, state: FSMContext, db: Database):
    """Получить цену товара"""
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    data = await state.get_data()
    
    try:
        await db.add_product(
            category_id=data.get("category_id"),
            title=data.get("title"),
            desc=data.get("desc"),
            price=price
        )
        await state.clear()
        await message.answer(
            f"✅ Товар <b>«{data.get('title')}»</b> успешно добавлен!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении товара: {e}",
            reply_markup=admin_menu()
        )
        await state.clear()


# ==================== СПИСОК ТОВАРОВ ====================

@router.message(F.text == "📦 Товары")
async def show_products_list(message: Message, state: FSMContext, db: Database):
    """Показать список всех товаров"""
    await state.clear()
    
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    products = await db.get_products()
    
    if not products:
        await message.answer(
            "📭 В базе нет товаров.\n\n"
            "Добавьте товары через ➕ Товар",
            reply_markup=admin_menu()
        )
        return
    
    await message.answer(
        "📦 <b>Список товаров:</b>\n\n"
        "Выберите товар для управления:",
        reply_markup=products_keyboard(products)
    )


# ==================== РЕДАКТИРОВАНИЕ ТОВАРА ====================

@router.callback_query(F.data.startswith("prod_"))
async def product_actions(callback: CallbackQuery, db: Database):
    """Показать действия с товаром"""
    await callback.answer()
    
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=None
        )
        return
    
    from keyboards import product_admin_keyboard
    await callback.message.edit_text(
        f"📦 <b>{product.get('title')}</b>\n\n"
        f"💰 Цена: {product.get('price', 0):.2f} ₽\n"
        f"📝 Описание: {product.get('desc', 'Нет описания')}\n\n"
        f"Выберите действие:",
        reply_markup=product_admin_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("edit_price_"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начать редактирование цены"""
    await callback.answer()
    
    product_id = int(callback.data.split("_")[2])
    await state.set_state(EditPriceForm.price)
    await state.update_data(product_id=product_id)
    
    await callback.message.edit_text(
        "✏️ Введите новую цену товара:\n"
        "или /cancel для отмены"
    )


@router.message(EditPriceForm.price)
async def edit_price_finish(message: Message, state: FSMContext, db: Database):
    """Получить новую цену"""
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    data = await state.get_data()
    product_id = data.get("product_id")
    
    try:
        await db.update_product_price(product_id, price)
        await state.clear()
        await message.answer(
            "✅ Цена товара обновлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=admin_menu()
        )
        await state.clear()


@router.callback_query(F.data.startswith("edit_desc_"))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начать редактирование описания"""
    await callback.answer()
    
    product_id = int(callback.data.split("_")[2])
    await state.set_state(EditDescForm.desc)
    await state.update_data(product_id=product_id)
    
    await callback.message.edit_text(
        "📝 Введите новое описание товара:\n"
        "или /cancel для отмены"
    )


@router.message(EditDescForm.desc)
async def edit_desc_finish(message: Message, state: FSMContext, db: Database):
    """Получить новое описание"""
    desc = message.text.strip()
    
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте ещё раз:")
        return
    
    data = await state.get_data()
    product_id = data.get("product_id")
    
    try:
        await db.update_product_desc(product_id, desc)
        await state.clear()
        await message.answer(
            "✅ Описание товара обновлено!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=admin_menu()
        )
        await state.clear()


@router.callback_query(F.data.startswith("del_prod_"))
async def delete_product(callback: CallbackQuery, db: Database):
    """Удалить товар"""
    await callback.answer()
    
    product_id = int(callback.data.split("_")[2])
    
    try:
        await db.delete_product(product_id)
        await callback.message.edit_text(
            "🗑 Товар успешно удалён!",
            reply_markup=None
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении: {e}",
            reply_markup=None
        )


# ==================== НАЗАД ====================

@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext, db: Database):
    """Вернуться в главное меню"""
    await state.clear()
    
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin)
    )


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext, db: Database):
    """Отмена текущего действия"""
    await state.clear()
    
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu(is_admin)
    )
