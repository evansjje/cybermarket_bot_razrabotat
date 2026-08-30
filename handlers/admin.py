# handlers/admin.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm import State, FSMContext
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards import admin_menu, admin_product_actions, main_menu
from config import settings

router = Router()
db = Database()


class CategoryStates(StatesGroup):
    waiting_for_title = State()


class ProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_desc = State()
    waiting_for_price = State()


class EditPriceStates(StatesGroup):
    waiting_for_price = State()


class EditDescStates(StatesGroup):
    waiting_for_desc = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message):
    """Открытие админ-панели"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message):
    """Показ статистики бота"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await db.connect()
    stats = await db.get_stats()
    await db.close()

    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: <b>{stats.get('users', 0)}</b>\n"
        f"📦 Товаров: <b>{stats.get('products', 0)}</b>\n"
        f"📂 Категорий: <b>{stats.get('categories', 0)}</b>\n"
        f"🛒 Товаров в корзинах: <b>{stats.get('cart_items', 0)}</b>"
    )

    await message.answer(text, reply_markup=admin_menu())


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext):
    """Начало добавления категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await state.set_state(CategoryStates.waiting_for_title)
    await message.answer(
        "📝 Введите название новой категории:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(CategoryStates.waiting_for_title)
async def add_category_title(message: Message, state: FSMContext):
    """Получение названия категории"""
    title = message.text.strip()

    if title.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление категории отменено.", reply_markup=admin_menu())
        return

    if not title:
        await message.answer("⚠️ Название не может быть пустым. Попробуйте ещё раз:")
        return

    await db.connect()
    try:
        await db.add_category(title)
        await message.answer(f"✅ Категория <b>{title}</b> успешно добавлена!", reply_markup=admin_menu())
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении категории: {e}", reply_markup=admin_menu())
    finally:
        await db.close()
        await state.clear()


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext):
    """Начало добавления товара"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await db.connect()
    categories = await db.get_categories()
    await db.close()

    if not categories:
        await message.answer(
            "⚠️ Сначала добавьте хотя бы одну категорию!",
            reply_markup=admin_menu()
        )
        return

    await state.set_state(ProductStates.waiting_for_category)

    # Формируем список категорий
    text = "📂 <b>Выберите категорию для товара:</b>\n\n"
    for i, cat in enumerate(categories, 1):
        text += f"{i}. {cat.get('title', 'Категория')}\n"

    text += "\nОтправьте номер категории или её название:"

    await message.answer(text)


@router.message(ProductStates.waiting_for_category)
async def add_product_category(message: Message, state: FSMContext):
    """Выбор категории для товара"""
    user_input = message.text.strip()

    if user_input.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return

    await db.connect()
    categories = await db.get_categories()

    # Поиск категории по номеру или названию
    selected_cat = None
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(categories):
            selected_cat = categories[idx]
    else:
        for cat in categories:
            if cat.get('title', '').lower() == user_input.lower():
                selected_cat = cat
                break

    if not selected_cat:
        await db.close()
        await message.answer("⚠️ Категория не найдена. Попробуйте ещё раз:")
        return

    await state.update_data(category_id=selected_cat['id'])
    await state.set_state(ProductStates.waiting_for_title)
    await db.close()

    await message.answer(
        f"📝 Введите название товара для категории <b>{selected_cat.get('title', '')}</b>:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(ProductStates.waiting_for_title)
async def add_product_title(message: Message, state: FSMContext):
    """Получение названия товара"""
    title = message.text.strip()

    if title.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return

    if not title:
        await message.answer("⚠️ Название не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(title=title)
    await state.set_state(ProductStates.waiting_for_desc)

    await message.answer(
        "📝 Введите описание товара:\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(ProductStates.waiting_for_desc)
async def add_product_desc(message: Message, state: FSMContext):
    """Получение описания товара"""
    desc = message.text.strip()

    if desc.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return

    if not desc:
        await message.answer("⚠️ Описание не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(desc=desc)
    await state.set_state(ProductStates.waiting_for_price)

    await message.answer(
        "💰 Введите цену товара (в рублях):\n"
        "(или отправьте /cancel для отмены)"
    )


@router.message(ProductStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    """Получение цены товара"""
    price_text = message.text.strip()

    if price_text.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return

    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    category_id = data.get('category_id')
    title = data.get('title')
    desc = data.get('desc')

    await db.connect()
    try:
        await db.add_product(category_id, title, desc, price)
        await message.answer(
            f"✅ Товар <b>{title}</b> успешно добавлен!\n"
            f"💰 Цена: {price}₽",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении товара: {e}", reply_markup=admin_menu())
    finally:
        await db.close()
        await state.clear()


@router.message(F.text == '📦 Товары')
async def show_all_products(message: Message):
    """Показ всех товаров для администрирования"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await db.connect()
    products = await db.get_products()
    await db.close()

    if not products:
        await message.answer(
            "📦 В базе пока нет товаров.\n"
            "Добавьте товары через кнопку ➕ Товар",
            reply_markup=admin_menu()
        )
        return

    text = "📦 <b>Все товары:</b>\n\n"
    for i, prod in enumerate(products, 1):
        text += (
            f"{i}. <b>{prod.get('title', 'Товар')}</b>\n"
            f"   💰 {prod.get('price', 0)}₽\n"
            f"   📝 {prod.get('desc', 'Нет описания')[:50]}...\n\n"
        )

    await message.answer(text, reply_markup=admin_menu())

    # Показываем товары с инлайн-кнопками
    for prod in products:
        product_id = prod.get('id')
        text = (
            f"🛍 <b>{prod.get('title', 'Товар')}</b>\n"
            f"💰 Цена: {prod.get('price', 0)}₽\n"
            f"📝 Описание: {prod.get('desc', 'Нет описания')}"
        )
        await message.answer(text, reply_markup=admin_product_actions(product_id))


@router.callback_query(F.data.startswith('edit_price:'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало изменения цены товара"""
    await callback.answer()

    product_id = int(callback.data.split(':')[1])

    await db.connect()
    product = await db.get_product_by_id(product_id)
    await db.close()

    if not product:
        try:
            await callback.message.edit_text("❌ Товар не найден.")
        except Exception:
            pass
        return

    await state.set_state(EditPriceStates.waiting_for_price)
    await state.update_data(product_id=product_id)

    try:
        await callback.message.edit_text(
            f"✏️ Текущая цена товара <b>{product.get('title', '')}</b>: {product.get('price', 0)}₽\n\n"
            "Введите новую цену:"
        )
    except Exception:
        pass


@router.message(EditPriceStates.waiting_for_price)
async def edit_price_finish(message: Message, state: FSMContext):
    """Получение новой цены"""
    price_text = message.text.strip()

    if price_text.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Изменение цены отменено.", reply_markup=admin_menu())
        return

    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (положительное число):")
        return

    data = await state.get_data()
    product_id = data.get('product_id')

    await db.connect()
    try:
        await db.update_product_price(product_id, price)
        await message.answer(f"✅ Цена товара обновлена! Новая цена: {price}₽", reply_markup=admin_menu())
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении цены: {e}", reply_markup=admin_menu())
    finally:
        await db.close()
        await state.clear()


@router.callback_query(F.data.startswith('edit_desc:'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext):
    """Начало изменения описания товара"""
    await callback.answer()

    product_id = int(callback.data.split(':')[1])

    await db.connect()
    product = await db.get_product_by_id(product_id)
    await db.close()

    if not product:
        try:
            await callback.message.edit_text("❌ Товар не найден.")
        except Exception:
            pass
        return

    await state.set_state(EditDescStates.waiting_for_desc)
    await state.update_data(product_id=product_id)

    try:
        await callback.message.edit_text(
            f"📝 Текущее описание товара <b>{product.get('title', '')}</b>:\n"
            f"{product.get('desc', 'Нет описания')}\n\n"
            "Введите новое описание:"
        )
    except Exception:
        pass


@router.message(EditDescStates.waiting_for_desc)
async def edit_desc_finish(message: Message, state: FSMContext):
    """Получение нового описания"""
    desc = message.text.strip()

    if desc.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Изменение описания отменено.", reply_markup=admin_menu())
        return

    if not desc:
        await message.answer("⚠️ Описание не может быть пустым. Попробуйте ещё раз:")
        return

    data = await state.get_data()
    product_id = data.get('product_id')

    await db.connect()
    try:
        await db.update_product_desc(product_id, desc)
        await message.answer("✅ Описание товара обновлено!", reply_markup=admin_menu())
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении описания: {e}", reply_markup=admin_menu())
    finally:
        await db.close()
        await state.clear()


@router.callback_query(F.data.startswith('delete_product:'))
async def delete_product(callback: CallbackQuery):
    """Удаление товара"""
    await callback.answer()

    product_id = int(callback.data.split(':')[1])

    await db.connect()
    try:
        await db.delete_product(product_id)
        await callback.message.edit_text("✅ Товар успешно удалён!")
    except Exception as e:
        try:
            await callback.message.edit_text(f"❌ Ошибка при удалении товара: {e}")
        except Exception:
            pass
    finally:
        await db.close()


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu(is_admin)
    )
