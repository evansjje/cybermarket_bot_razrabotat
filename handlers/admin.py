from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from contextlib import suppress

from database import Database
from keyboards import admin_menu, main_menu, products_keyboard
from config import settings

router = Router()


class CategoryStates(StatesGroup):
    waiting_for_title = State()


class ProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()


class EditProductStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_description = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(F.text == '/admin')
async def admin_panel(message: Message, db: Database) -> None:
    """Открытие админ-панели"""
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
async def show_stats(message: Message, db: Database) -> None:
    """Показ статистики бота"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_stats()

    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats.get('users', 0)}</b>\n"
        f"📦 Товаров: <b>{stats.get('products', 0)}</b>\n"
        f"🗂 Категорий: <b>{stats.get('categories', 0)}</b>\n"
        f"🛒 Заказов в корзинах: <b>{stats.get('cart_items', 0)}</b>"
    )

    await message.answer(text, reply_markup=admin_menu())


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext, db: Database) -> None:
    """Начало добавления категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await state.set_state(CategoryStates.waiting_for_title)
    await message.answer(
        "➕ Введите название новой категории:\n"
        "Для отмены отправьте /cancel"
    )


@router.message(CategoryStates.waiting_for_title)
async def add_category_title(message: Message, state: FSMContext, db: Database) -> None:
    """Получение названия категории"""
    title = message.text.strip()

    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return

    try:
        await db.add_category(title)
        await message.answer(
            f"✅ Категория <b>{title}</b> успешно добавлена!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении категории: {str(e)}\n"
            "Возможно, такая категория уже существует.",
            reply_markup=admin_menu()
        )
    finally:
        await state.clear()


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext, db: Database) -> None:
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

    await state.set_state(ProductStates.waiting_for_category)

    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat.get('title', 'Без названия'),
            callback_data=f"addprod_cat_{cat.get('id', 0)}"
        )
    builder.adjust(1)

    await message.answer(
        "➕ Выберите категорию для нового товара:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith('addprod_cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбор категории для товара"""
    await callback.answer()

    category_id = int(callback.data.split('_')[2])
    await state.update_data(category_id=category_id)
    await state.set_state(ProductStates.waiting_for_title)

    await callback.message.answer(
        "📝 Введите название товара:\n"
        "Для отмены отправьте /cancel"
    )


@router.message(ProductStates.waiting_for_title)
async def add_product_title(message: Message, state: FSMContext, db: Database) -> None:
    """Получение названия товара"""
    title = message.text.strip()

    if not title:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return

    await state.update_data(title=title)
    await state.set_state(ProductStates.waiting_for_description)

    await message.answer(
        "📝 Введите описание товара:\n"
        "Для отмены отправьте /cancel"
    )


@router.message(ProductStates.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext, db: Database) -> None:
    """Получение описания товара"""
    description = message.text.strip()

    if not description:
        await message.answer("❌ Описание не может быть пустым. Попробуйте еще раз:")
        return

    await state.update_data(description=description)
    await state.set_state(ProductStates.waiting_for_price)

    await message.answer(
        "💰 Введите цену товара (в рублях):\n"
        "Для отмены отправьте /cancel"
    )


@router.message(ProductStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext, db: Database) -> None:
    """Получение цены товара"""
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число). Попробуйте еще раз:")
        return

    data = await state.get_data()
    category_id = data.get('category_id')
    title = data.get('title')
    description = data.get('description')

    try:
        await db.add_product(
            category_id=category_id,
            title=title,
            desc=description,
            price=price
        )
        await message.answer(
            f"✅ Товар <b>{title}</b> успешно добавлен!\n"
            f"💰 Цена: {price} ₽",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении товара: {str(e)}",
            reply_markup=admin_menu()
        )
    finally:
        await state.clear()


@router.message(F.text == '📦 Товары')
async def show_all_products(message: Message, db: Database) -> None:
    """Показ всех товаров для управления"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    products = await db.get_products()
    if not products:
        await message.answer(
            "📭 В базе пока нет товаров.",
            reply_markup=admin_menu()
        )
        return

    await message.answer(
        "📦 <b>Все товары:</b>\n\n"
        "Выберите товар для управления:",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(F.data.startswith('prod_'))
async def admin_product_card(callback: CallbackQuery, db: Database) -> None:
    """Карточка товара в админке"""
    await callback.answer()

    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)

    if not product:
        await callback.message.answer("❌ Товар не найден.")
        return

    text = (
        f"📦 <b>{product.get('title', 'Без названия')}</b>\n\n"
        f"📝 {product.get('description', 'Описание отсутствует')}\n\n"
        f"💰 Цена: <b>{product.get('price', 0)} ₽</b>\n"
        f"🆔 ID: {product.get('id', 0)}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✏️ Цена",
            callback_data=f"editprice_{product_id}"
        ),
        InlineKeyboardButton(
            text="📝 Описание",
            callback_data=f"editdesc_{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"deleteprod_{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_products"
        )
    )

    with suppress(Exception):
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data == 'back_to_products')
async def back_to_products(callback: CallbackQuery, db: Database) -> None:
    """Возврат к списку товаров"""
    await callback.answer()

    products = await db.get_products()
    if not products:
        await callback.message.answer(
            "📭 В базе пока нет товаров.",
            reply_markup=admin_menu()
        )
        return

    with suppress(Exception):
        await callback.message.edit_text(
            "📦 <b>Все товары:</b>\n\n"
            "Выберите товар для управления:",
            reply_markup=products_keyboard(products)
        )


@router.callback_query(F.data.startswith('editprice_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начало изменения цены"""
    await callback.answer()

    product_id = int(callback.data.split('_')[1])
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductStates.waiting_for_price)

    await callback.message.answer(
        "💰 Введите новую цену товара:\n"
        "Для отмены отправьте /cancel"
    )


@router.message(EditProductStates.waiting_for_price)
async def edit_price_finish(message: Message, state: FSMContext, db: Database) -> None:
    """Получение новой цены"""
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число). Попробуйте еще раз:")
        return

    data = await state.get_data()
    product_id = data.get('product_id')

    try:
        await db.update_product_price(product_id, price)
        await message.answer(
            f"✅ Цена товара обновлена до {price} ₽",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при обновлении цены: {str(e)}",
            reply_markup=admin_menu()
        )
    finally:
        await state.clear()


@router.callback_query(F.data.startswith('editdesc_'))
async def edit_description_start(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начало изменения описания"""
    await callback.answer()

    product_id = int(callback.data.split('_')[1])
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductStates.waiting_for_description)

    await callback.message.answer(
        "📝 Введите новое описание товара:\n"
        "Для отмены отправьте /cancel"
    )


@router.message(EditProductStates.waiting_for_description)
async def edit_description_finish(message: Message, state: FSMContext, db: Database) -> None:
    """Получение нового описания"""
    description = message.text.strip()

    if not description:
        await message.answer("❌ Описание не может быть пустым. Попробуйте еще раз:")
        return

    data = await state.get_data()
    product_id = data.get('product_id')

    try:
        await db.update_product_desc(product_id, description)
        await message.answer(
            "✅ Описание товара обновлено!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при обновлении описания: {str(e)}",
            reply_markup=admin_menu()
        )
    finally:
        await state.clear()


@router.callback_query(F.data.startswith('deleteprod_'))
async def delete_product(callback: CallbackQuery, db: Database) -> None:
    """Удаление товара"""
    await callback.answer()

    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)

    if not product:
        await callback.message.answer("❌ Товар не найден.")
        return

    title = product.get('title', 'Без названия')

    try:
        await db.delete_product(product_id)
        await callback.message.answer(
            f"🗑 Товар <b>{title}</b> удален!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка при удалении товара: {str(e)}",
            reply_markup=admin_menu()
        )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, db: Database) -> None:
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(F.text == '/cancel')
async def cancel_operation(message: Message, state: FSMContext) -> None:
    """Отмена текущей операции"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активной операции для отмены.")
        return

    await state.clear()
    await message.answer(
        "❌ Операция отменена.",
        reply_markup=admin_menu()
    )
