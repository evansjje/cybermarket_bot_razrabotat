# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database import Database
from keyboards import admin_menu_kb, main_menu_kb, back_to_admin_kb, product_card_kb
from config import settings

router = Router()
db = Database()


class AdminStates(StatesGroup):
    """Состояния для админ-панели."""
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()
    waiting_product_stock = State()


async def show_admin_panel(message: Message):
    """Показать админ-панель (используется другими модулями)."""
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Открыть админ-панель (только для админа)."""
    await show_admin_panel(message)


@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel_button(message: Message):
    """Открыть админ-панель через кнопку."""
    await show_admin_panel(message)


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику бота."""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён", show_alert=True)
        return
    
    stats = await db.get_stats()
    
    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📦 Товаров: <b>{stats['products']}</b>\n"
        f"📂 Категорий: <b>{stats['categories']}</b>\n"
        f"🛒 Товаров в корзинах: <b>{stats['cart_items']}</b>\n"
        f"💰 Общая сумма корзин: <b>{stats['cart_total']}₽</b>\n"
        f"📦 Общий остаток товаров: <b>{stats['total_stock']}</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=back_to_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара."""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Введите название товара:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_product_name)
    await callback.answer()


@router.message(AdminStates.waiting_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    """Получить название товара."""
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа.")
        return
    
    product_name = message.text.strip()
    if len(product_name) < 2 or len(product_name) > 100:
        await message.answer("❌ Название должно быть от 2 до 100 символов. Попробуйте ещё раз:")
        return
    
    await state.update_data(product_name=product_name)
    await message.answer(
        f"✅ Название: <b>{product_name}</b>\n\n"
        "Теперь введите описание товара:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_product_description)


@router.message(AdminStates.waiting_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    """Получить описание товара."""
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа.")
        return
    
    description = message.text.strip()
    if len(description) < 5 or len(description) > 500:
        await message.answer("❌ Описание должно быть от 5 до 500 символов. Попробуйте ещё раз:")
        return
    
    await state.update_data(product_description=description)
    await message.answer(
        f"✅ Описание: <b>{description}</b>\n\n"
        "Введите цену товара (в рублях, число):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_product_price)


@router.message(AdminStates.waiting_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получить цену товара."""
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа.")
        return
    
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0 or price > 1000000:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число, например 199.99):")
        return
    
    await state.update_data(product_price=price)
    
    # Получаем категории для выбора
    categories = await db.get_categories()
    if not categories:
        await message.answer("❌ Нет категорий. Сначала добавьте категорию вручную в БД.")
        await state.clear()
        return
    
    # Формируем клавиатуру с категориями
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📂 {cat['name']}", callback_data=f"admin_cat_{cat['id']}")]
        for cat in categories
    ])
    
    await message.answer(
        f"✅ Цена: <b>{price}₽</b>\n\n"
        "Выберите категорию:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_product_category)


@router.callback_query(AdminStates.waiting_product_category, F.data.startswith("admin_cat_"))
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    """Получить категорию товара."""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    
    await state.update_data(product_category_id=category_id)
    await callback.message.edit_text(
        f"✅ Категория выбрана.\n\n"
        f"📦 Товар: <b>{data['product_name']}</b>\n"
        f"📝 Описание: <b>{data['product_description']}</b>\n"
        f"💰 Цена: <b>{data['product_price']}₽</b>\n\n"
        "Введите количество на складе (целое число):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_product_stock)
    await callback.answer()


@router.message(AdminStates.waiting_product_stock)
async def admin_add_product_stock(message: Message, state: FSMContext):
    """Получить количество товара и сохранить."""
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа.")
        return
    
    try:
        stock = int(message.text.strip())
        if stock < 0 or stock > 100000:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное количество (целое число от 0 до 100000):")
        return
    
    data = await state.get_data()
    
    # Добавляем товар в базу
    product_id = await db.add_product(
        category_id=data['product_category_id'],
        name=data['product_name'],
        description=data['product_description'],
        price=data['product_price'],
        stock=stock
    )
    
    await message.answer(
        "✅ <b>Товар успешно добавлен!</b>\n\n"
        f"🆔 ID: <code>{product_id}</code>\n"
        f"📦 Название: <b>{data['product_name']}</b>\n"
        f"📝 Описание: <b>{data['product_description']}</b>\n"
        f"💰 Цена: <b>{data['product_price']}₽</b>\n"
        f"📊 Остаток: <b>{stock} шт.</b>",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )
    
    await state.clear()


@router.callback_query(F.data == "admin_products")
async def admin_products_list(callback: CallbackQuery):
    """Показать список всех товаров."""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён", show_alert=True)
        return
    
    products = await db.get_all_products()
    
    if not products:
        await callback.message.edit_text(
            "📦 <b>Список товаров пуст.</b>\n\n"
            "Добавьте первый товар через админ-панель.",
            reply_markup=back_to_admin_kb(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    text = "📦 <b>Все товары:</b>\n\n"
    for prod in products:
        text += (
            f"🆔 <code>{prod['id']}</code> | <b>{prod['name']}</b>\n"
            f"   💰 {prod['price']}₽ | 📊 Остаток: {prod['stock']} шт.\n"
            f"   📂 Категория ID: {prod['category_id']}\n\n"
        )
    
    await callback.message.edit_text(text, reply_markup=back_to_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Вернуться в админ-меню."""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel_text(message: Message):
    """Обработка текстовой кнопки админ-панели."""
    await show_admin_panel(message)
