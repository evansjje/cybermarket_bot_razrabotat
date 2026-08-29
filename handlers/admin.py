from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import admin_menu, main_menu
from config import settings

router = Router()
db = Database()


class AdminStates(StatesGroup):
    waiting_category_name = State()
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()


@router.message(F.text == '⚡ Админ-панель')
async def admin_panel(message: Message):
    """Показать админ-панель"""
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return
    
    await message.answer(
        "⚡ Админ-панель\nВыберите действие:",
        reply_markup=admin_menu()
    )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message):
    """Вернуться в главное меню"""
    is_admin = message.from_user.id in settings.ADMIN_IDS
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin)
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message):
    """Показать статистику бота"""
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    
    stats = await db.get_stats()
    referrals = await db.get_referrals_count()
    
    text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📦 Заказов: <b>{stats['orders']}</b>\n"
        f"💰 Выручка: <b>{stats['revenue']} ₽</b>\n"
        f"👥 Рефералов: <b>{referrals}</b>"
    )
    
    await message.answer(text)


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext):
    """Начать добавление категории"""
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    
    await state.set_state(AdminStates.waiting_category_name)
    await message.answer(
        "Введите название новой категории:\n"
        "Или отправьте /cancel для отмены"
    )


@router.message(AdminStates.waiting_category_name)
async def add_category_name(message: Message, state: FSMContext):
    """Получить название категории"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление категории отменено")
        return
    
    category_name = message.text.strip()
    
    try:
        await db.db.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (category_name,)
        )
        await db.db.commit()
        await message.answer(f"✅ Категория «{category_name}» добавлена!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext):
    """Начать добавление товара"""
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    
    await state.set_state(AdminStates.waiting_product_name)
    await message.answer(
        "Введите название товара:\n"
        "Или отправьте /cancel для отмены"
    )


@router.message(AdminStates.waiting_product_name)
async def add_product_name(message: Message, state: FSMContext):
    """Получить название товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено")
        return
    
    await state.update_data(product_name=message.text.strip())
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer(
        "Введите описание товара:\n"
        "Или отправьте /cancel для отмены"
    )


@router.message(AdminStates.waiting_product_description)
async def add_product_description(message: Message, state: FSMContext):
    """Получить описание товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено")
        return
    
    await state.update_data(product_description=message.text.strip())
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        "Введите цену товара (в рублях):\n"
        "Или отправьте /cancel для отмены"
    )


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: Message, state: FSMContext):
    """Получить цену товара"""
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено")
        return
    
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число)")
        return
    
    await state.update_data(product_price=price)
    
    # Показать категории для выбора
    categories = await db.get_categories()
    if not categories:
        await message.answer("❌ Сначала добавьте категорию!")
        await state.clear()
        return
    
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.row(InlineKeyboardButton(
            text=cat['name'],
            callback_data=f'admin_cat_{cat["id"]}'
        ))
    kb.row(InlineKeyboardButton(
        text='❌ Отмена',
        callback_data='admin_cancel'
    ))
    
    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        "Выберите категорию для товара:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith('admin_cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext):
    """Получить категорию товара"""
    await callback.answer()
    
    if callback.data == 'admin_cancel':
        await state.clear()
        await callback.message.edit_text("❌ Добавление товара отменено")
        return
    
    category_id = int(callback.data.split('_')[2])
    data = await state.get_data()
    
    try:
        await db.db.execute(
            """INSERT INTO products (category_id, name, description, price) 
               VALUES (?, ?, ?, ?)""",
            (category_id, data['product_name'], data['product_description'], data['product_price'])
        )
        await db.db.commit()
        await callback.message.edit_text(
            f"✅ Товар «{data['product_name']}» добавлен!"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await state.clear()


@router.callback_query(F.data == 'admin_cancel')
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления товара"""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("❌ Добавление товара отменено")


@router.message(F.text == '📦 Товары')
async def show_products_admin(message: Message):
    """Показать все товары для управления"""
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer("❌ Нет категорий!")
        return
    
    text = "📦 <b>Все товары:</b>\n\n"
    kb = InlineKeyboardBuilder()
    
    for cat in categories:
        products = await db.get_products(cat['id'])
        if products:
            text += f"<b>{cat['name']}:</b>\n"
            for prod in products:
                text += f"  • {prod['name']} — {prod['price']} ₽\n"
                kb.row(InlineKeyboardButton(
                    text=f"🗑 {prod['name']}",
                    callback_data=f'del_prod_{prod["id"]}'
                ))
    
    if not text.endswith("\n\n"):
        text += "\n"
    
    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith('del_prod_'))
async def delete_product(callback: CallbackQuery):
    """Удалить товар"""
    await callback.answer()
    
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return
    
    try:
        await db.delete_product(product_id)
        await callback.answer(f"✅ Товар «{product['name']}» удален!", show_alert=True)
        
        # Обновить список товаров
        categories = await db.get_categories()
        text = "📦 <b>Все товары:</b>\n\n"
        kb = InlineKeyboardBuilder()
        
        for cat in categories:
            products = await db.get_products(cat['id'])
            if products:
                text += f"<b>{cat['name']}:</b>\n"
                for prod in products:
                    text += f"  • {prod['name']} — {prod['price']} ₽\n"
                    kb.row(InlineKeyboardButton(
                        text=f"🗑 {prod['name']}",
                        callback_data=f'del_prod_{prod["id"]}'
                    ))
        
        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
        except Exception:
            pass
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.message(Command('cancel'))
async def cancel_command(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активных действий")
        return
    
    await state.clear()
    await message.answer("❌ Действие отменено")
