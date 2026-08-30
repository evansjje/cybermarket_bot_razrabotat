# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from database import Database
from keyboards import (
    admin_menu,
    admin_products_keyboard,
    admin_product_actions_keyboard,
    main_menu,
    categories_keyboard
)

router = Router()


class AdminStates(StatesGroup):
    """Состояния для админ-панели."""
    waiting_category_title = State()
    waiting_product_category = State()
    waiting_product_title = State()
    waiting_product_desc = State()
    waiting_product_price = State()
    waiting_edit_price = State()
    waiting_edit_desc = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом."""
    return user_id in settings.ADMIN_IDS


@router.message(F.text == '⚡ Админ-панель')
@router.message(F.text == '/admin')
async def admin_panel(message: Message, db: Database):
    """Открытие админ-панели."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора!")
        return

    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu(),
        parse_mode='HTML'
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message, db: Database):
    """Показ статистики бота."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора!")
        return

    stats = await db.get_stats()

    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats.get('users', 0)}</b>\n"
        f"📦 Товаров: <b>{stats.get('products', 0)}</b>\n"
        f"📂 Категорий: <b>{stats.get('categories', 0)}</b>\n"
        f"🛒 Заказов в корзинах: <b>{stats.get('cart_items', 0)}</b>"
    )

    await message.answer(text, parse_mode='HTML')


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext, db: Database):
    """Начало добавления категории."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора!")
        return

    await state.set_state(AdminStates.waiting_category_title)
    await message.answer(
        "📝 Введите название новой категории:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(AdminStates.waiting_category_title)
async def add_category_finish(message: Message, state: FSMContext, db: Database):
    """Завершение добавления категории."""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    title = message.text.strip()
    if not title:
        await message.answer("⚠️ Название не может быть пустым. Попробуйте ещё раз:")
        return

    try:
        await db.add_category(title)
        await state.clear()
        await message.answer(
            f"✅ Категория <b>«{title}»</b> успешно добавлена!",
            reply_markup=admin_menu(),
            parse_mode='HTML'
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при добавлении категории: {str(e)}",
            reply_markup=admin_menu()
        )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database):
    """Начало добавления товара."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора!")
        return

    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "⚠️ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        return

    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        "📂 Выберите категорию для товара:",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(AdminStates.waiting_product_category, F.data.startswith('cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext, db: Database):
    """Выбор категории для товара."""
    await callback.answer()

    try:
        category_id = int(callback.data.split('_')[1])
        await state.update_data(product_category_id=category_id)
        await state.set_state(AdminStates.waiting_product_title)

        await callback.message.edit_text(
            "📝 Введите название товара:\n"
            "(или отправьте /cancel для отмены)"
        )
    except Exception:
        await callback.message.edit_text("❌ Ошибка. Попробуйте ещё раз.")


@router.message(AdminStates.waiting_product_title)
async def add_product_title(message: Message, state: FSMContext, db: Database):
    """Ввод названия товара."""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    title = message.text.strip()
    if not title:
        await message.answer("⚠️ Название не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(product_title=title)
    await state.set_state(AdminStates.waiting_product_desc)
    await message.answer(
        "📝 Введите описание товара:\n"
        "(или отправьте /skip чтобы пропустить)"
    )


@router.message(AdminStates.waiting_product_desc)
async def add_product_desc(message: Message, state: FSMContext, db: Database):
    """Ввод описания товара."""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    desc = message.text.strip()
    if message.text == '/skip':
        desc = ""

    await state.update_data(product_desc=desc)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        "💰 Введите цену товара (в рублях):\n"
        "(например: 199.99)"
    )


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: Message, state: FSMContext, db: Database):
    """Ввод цены товара."""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=admin_menu())
        return

    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError("Цена должна быть положительной")

        data = await state.get_data()
        category_id = data.get('product_category_id')
        title = data.get('product_title')
        desc = data.get('product_desc', '')

        await db.add_product(category_id, title, desc, price)
        await state.clear()

        await message.answer(
            f"✅ Товар <b>«{title}»</b> успешно добавлен!\n"
            f"💰 Цена: {price}₽",
            reply_markup=admin_menu(),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (число). Попробуйте ещё раз:")
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка при добавлении товара: {str(e)}",
            reply_markup=admin_menu()
        )


@router.message(F.text == '📦 Товары')
async def show_admin_products(message: Message, db: Database):
    """Показ списка товаров для админа."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора!")
        return

    products = await db.get_products()
    if not products:
        await message.answer(
            "📭 В базе нет товаров.\n"
            "Добавьте товары через ➕ Товар",
            reply_markup=admin_menu()
        )
        return

    await message.answer(
        "📦 <b>Список товаров:</b>\n"
        "Выберите товар для управления:",
        reply_markup=admin_products_keyboard(products),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith('adm_prod_'))
async def admin_product_actions(callback: CallbackQuery, db: Database):
    """Действия с товаром в админке."""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[2])
        product = await db.get_product_by_id(product_id)

        if not product:
            await callback.message.edit_text(
                "❌ Товар не найден.",
                reply_markup=admin_menu()
            )
            return

        text = (
            f"📦 <b>{product.get('title', 'Товар')}</b>\n\n"
            f"📝 {product.get('desc', 'Описание отсутствует')}\n"
            f"💰 Цена: <b>{product.get('price', 0)}₽</b>\n\n"
            f"Выберите действие:"
        )

        await callback.message.edit_text(
            text,
            reply_markup=admin_product_actions_keyboard(product_id),
            parse_mode='HTML'
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало редактирования цены."""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[2])
        await state.update_data(edit_product_id=product_id)
        await state.set_state(AdminStates.waiting_edit_price)

        await callback.message.edit_text(
            "💰 Введите новую цену товара:\n"
            "(или отправьте /cancel для отмены)"
        )
    except Exception:
        pass


@router.message(AdminStates.waiting_edit_price)
async def edit_price_finish(message: Message, state: FSMContext, db: Database):
    """Завершение редактирования цены."""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Редактирование отменено.", reply_markup=admin_menu())
        return

    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError("Цена должна быть положительной")

        data = await state.get_data()
        product_id = data.get('edit_product_id')

        await db.update_product_price(product_id, price)
        await state.clear()

        product = await db.get_product_by_id(product_id)
        await message.answer(
            f"✅ Цена товара <b>«{product.get('title', 'Товар')}»</b> обновлена!\n"
            f"💰 Новая цена: {price}₽",
            reply_markup=admin_menu(),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (число). Попробуйте ещё раз:")
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=admin_menu()
        )


@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало редактирования описания."""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[2])
        await state.update_data(edit_product_id=product_id)
        await state.set_state(AdminStates.waiting_edit_desc)

        await callback.message.edit_text(
            "📝 Введите новое описание товара:\n"
            "(или отправьте /cancel для отмены)"
        )
    except Exception:
        pass


@router.message(AdminStates.waiting_edit_desc)
async def edit_desc_finish(message: Message, state: FSMContext, db: Database):
    """Завершение редактирования описания."""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Редактирование отменено.", reply_markup=admin_menu())
        return

    desc = message.text.strip()
    if not desc:
        await message.answer("⚠️ Описание не может быть пустым. Попробуйте ещё раз:")
        return

    data = await state.get_data()
    product_id = data.get('edit_product_id')

    await db.update_product_desc(product_id, desc)
    await state.clear()

    product = await db.get_product_by_id(product_id)
    await message.answer(
        f"✅ Описание товара <b>«{product.get('title', 'Товар')}»</b> обновлено!",
        reply_markup=admin_menu(),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith('del_'))
async def delete_product(callback: CallbackQuery, db: Database):
    """Удаление товара."""
    await callback.answer()

    try:
        product_id = int(callback.data.split('_')[1])
        product = await db.get_product_by_id(product_id)

        if not product:
            await callback.message.edit_text(
                "❌ Товар не найден.",
                reply_markup=admin_menu()
            )
            return

        title = product.get('title', 'Товар')
        await db.delete_product(product_id)

        products = await db.get_products()
        if products:
            await callback.message.edit_text(
                f"🗑 Товар <b>«{title}»</b> удалён!\n\n"
                f"📦 Оставшиеся товары:",
                reply_markup=admin_products_keyboard(products),
                parse_mode='HTML'
            )
        else:
            await callback.message.edit_text(
                f"🗑 Товар <b>«{title}»</b> удалён!\n"
                "В базе больше нет товаров.",
                reply_markup=admin_menu()
            )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_admin_products')
async def back_to_admin_products(callback: CallbackQuery, db: Database):
    """Возврат к списку товаров в админке."""
    await callback.answer()

    try:
        products = await db.get_products()
        if products:
            await callback.message.edit_text(
                "📦 <b>Список товаров:</b>\n"
                "Выберите товар для управления:",
                reply_markup=admin_products_keyboard(products),
                parse_mode='HTML'
            )
        else:
            await callback.message.edit_text(
                "📭 В базе нет товаров.",
                reply_markup=admin_menu()
            )
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_admin')
async def back_to_admin(callback: CallbackQuery):
    """Возврат в админ-панель."""
    await callback.answer()

    try:
        await callback.message.edit_text(
            "⚡ <b>Админ-панель</b>\n\n"
            "Выберите действие:",
            reply_markup=admin_menu(),
            parse_mode='HTML'
        )
    except Exception:
        pass


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database):
    """Возврат в главное меню."""
    user_id = message.from_user.id
    is_admin = is_admin(user_id)

    await message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu(is_admin)
    )
