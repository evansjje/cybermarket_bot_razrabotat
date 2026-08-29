from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm import FSMContext, State
from aiogram.fsm.state import StatesGroup

from database import Database
from keyboards import admin_menu, main_menu, products_keyboard
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


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Регистрация пользователя в БД
    await db.db.execute(
        "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )
    await db.db.commit()

    # Проверка, является ли пользователь администратором
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        f"👋 Добро пожаловать, {first_name or 'пользователь'}!\n\n"
        "🛍 Здесь вы можете приобрести цифровые товары.\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message, db: Database):
    """Показать админ-панель"""
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
async def show_stats(message: Message, db: Database):
    """Показать статистику"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_stats()
    await message.answer(
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: {stats.get('users', 0)}\n"
        f"📦 Товаров: {stats.get('products', 0)}\n"
        f"🛒 Заказов: {stats.get('orders', 0)}"
    )


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext):
    """Начало добавления категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await state.set_state(CategoryForm.title)
    await message.answer(
        "📝 Введите название новой категории:\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(CategoryForm.title)
async def add_category_finish(message: Message, state: FSMContext, db: Database):
    """Завершение добавления категории"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return

    try:
        await db.add_category(title)
        await message.answer(
            f"✅ Категория «{title}» успешно добавлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении категории: {e}",
            reply_markup=admin_menu()
        )
    finally:
        await state.clear()


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database):
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

    await state.set_state(ProductForm.category_id)
    await message.answer(
        "📝 Выберите категорию для товара:\n\n"
        + "\n".join([f"{cat['id']}. {cat['title']}" for cat in categories]) +
        "\n\nВведите ID категории или /cancel для отмены."
    )


@router.message(ProductForm.category_id)
async def add_product_category(message: Message, state: FSMContext, db: Database):
    """Выбор категории для товара"""
    try:
        category_id = int(message.text.strip())
        categories = await db.get_categories()
        if not any(cat['id'] == category_id for cat in categories):
            await message.answer("❌ Категория не найдена. Попробуйте ещё раз:")
            return

        await state.update_data(category_id=category_id)
        await state.set_state(ProductForm.title)
        await message.answer(
            "📝 Введите название товара:\n"
            "Или отправьте /cancel для отмены."
        )
    except ValueError:
        await message.answer("❌ Введите корректный ID категории:")


@router.message(ProductForm.title)
async def add_product_title(message: Message, state: FSMContext):
    """Ввод названия товара"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(title=title)
    await state.set_state(ProductForm.desc)
    await message.answer(
        "📝 Введите описание товара:\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(ProductForm.desc)
async def add_product_desc(message: Message, state: FSMContext):
    """Ввод описания товара"""
    desc = message.text.strip()
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(desc=desc)
    await state.set_state(ProductForm.price)
    await message.answer(
        "💰 Введите цену товара (в рублях):\n"
        "Или отправьте /cancel для отмены."
    )


@router.message(ProductForm.price)
async def add_product_price(message: Message, state: FSMContext, db: Database):
    """Ввод цены товара и сохранение"""
    try:
        price = float(message.text.strip())
        if price <= 0:
            await message.answer("❌ Цена должна быть положительной. Попробуйте ещё раз:")
            return

        data = await state.get_data()
        await db.add_product(
            category_id=data['category_id'],
            title=data['title'],
            desc=data['desc'],
            price=price
        )

        await message.answer(
            f"✅ Товар «{data['title']}» успешно добавлен!",
            reply_markup=admin_menu()
        )
    except ValueError:
        await message.answer("❌ Введите корректную цену (число):")
    finally:
        await state.clear()


@router.message(F.text == '📦 Товары')
async def show_products(message: Message, db: Database):
    """Показать все товары"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    products = await db.get_products()
    if not products:
        await message.answer(
            "📭 Список товаров пуст.",
            reply_markup=admin_menu()
        )
        return

    await message.answer(
        "📦 <b>Все товары:</b>",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало редактирования цены"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[2])
        product = await db.get_product_by_id(product_id)
        if not product:
            await callback.message.edit_text("❌ Товар не найден.")
            return

        await state.update_data(product_id=product_id)
        await state.set_state(EditPriceForm.price)
        await callback.message.edit_text(
            f"💰 Текущая цена: {product['price']}₽\n"
            f"Введите новую цену:\n"
            f"Или отправьте /cancel для отмены."
        )
    except Exception:
        pass


@router.message(EditPriceForm.price)
async def edit_price_finish(message: Message, state: FSMContext, db: Database):
    """Завершение редактирования цены"""
    try:
        price = float(message.text.strip())
        if price <= 0:
            await message.answer("❌ Цена должна быть положительной. Попробуйте ещё раз:")
            return

        data = await state.get_data()
        await db.update_product_price(data['product_id'], price)
        await message.answer(
            f"✅ Цена обновлена!",
            reply_markup=admin_menu()
        )
    except ValueError:
        await message.answer("❌ Введите корректную цену (число):")
    finally:
        await state.clear()


@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало редактирования описания"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[2])
        product = await db.get_product_by_id(product_id)
        if not product:
            await callback.message.edit_text("❌ Товар не найден.")
            return

        await state.update_data(product_id=product_id)
        await state.set_state(EditDescForm.desc)
        await callback.message.edit_text(
            f"📝 Текущее описание: {product['desc']}\n\n"
            f"Введите новое описание:\n"
            f"Или отправьте /cancel для отмены."
        )
    except Exception:
        pass


@router.message(EditDescForm.desc)
async def edit_desc_finish(message: Message, state: FSMContext, db: Database):
    """Завершение редактирования описания"""
    desc = message.text.strip()
    if not desc:
        await message.answer("❌ Описание не может быть пустым. Попробуйте ещё раз:")
        return

    data = await state.get_data()
    await db.update_product_desc(data['product_id'], desc)
    await message.answer(
        f"✅ Описание обновлено!",
        reply_markup=admin_menu()
    )
    await state.clear()


@router.callback_query(F.data.startswith('del_prod_'))
async def delete_product(callback: CallbackQuery, db: Database):
    """Удаление товара"""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[2])
        await db.delete_product(product_id)
        await callback.message.edit_text(
            f"✅ Товар удалён!",
            reply_markup=admin_menu()
        )
    except Exception:
        pass


@router.message(F.text == '⬅️ Назад')
async def back_to_menu(message: Message, state: FSMContext, db: Database):
    """Возврат в главное меню"""
    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(Command('cancel'))
async def cancel_command(message: Message, state: FSMContext, db: Database):
    """Отмена действия"""
    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu(is_admin=is_admin)
    )
