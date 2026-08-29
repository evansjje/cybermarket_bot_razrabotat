from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart

from config import settings
from database import Database
from keyboards import admin_menu, main_menu, delete_product_buttons

router = Router()
db = Database()


class AdminStates(StatesGroup):
    waiting_category_name = State()
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(F.text == '⚡ Админ-панель')
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    await message.answer("⚡ Админ-панель", reply_markup=admin_menu())


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in settings.ADMIN_IDS
    await message.answer("Главное меню", reply_markup=main_menu(is_admin))


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    stats = await db.get_stats()
    referrals = await db.get_referrals_count()
    
    text = (
        f"📊 Статистика бота:\n\n"
        f"👥 Пользователей: {stats['users']}\n"
        f"📦 Заказов: {stats['orders']}\n"
        f"💰 Выручка: {stats['revenue']} ₽\n"
        f"👥 Рефералов: {referrals}"
    )
    await message.answer(text)


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    await state.set_state(AdminStates.waiting_category_name)
    await message.answer("Введите название новой категории (или /cancel для отмены):")


@router.message(AdminStates.waiting_category_name)
async def add_category_finish(message: Message, state: FSMContext):
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление категории отменено.", reply_markup=admin_menu())
        return
    
    category_name = message.text.strip()
    if not category_name:
        await message.answer("⚠️ Название категории не может быть пустым. Попробуйте еще раз:")
        return
    
    try:
        await db.db.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (category_name,)
        )
        await db.db.commit()
        await state.clear()
        await message.answer(f"✅ Категория «{category_name}» успешно добавлена!", reply_markup=admin_menu())
    except Exception:
        await message.answer("❌ Такая категория уже существует. Попробуйте другое название:")
        await state.clear()


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer("❌ Сначала добавьте хотя бы одну категорию!", reply_markup=admin_menu())
        return
    
    await state.set_state(AdminStates.waiting_product_name)
    await message.answer("Введите название товара (или /cancel для отмены):")


@router.message(AdminStates.waiting_product_name)
async def add_product_name(message: Message, state: FSMContext):
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return
    
    product_name = message.text.strip()
    if not product_name:
        await message.answer("⚠️ Название товара не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer("Введите описание товара (или /cancel для отмены):")


@router.message(AdminStates.waiting_product_description)
async def add_product_description(message: Message, state: FSMContext):
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return
    
    description = message.text.strip()
    if not description:
        await message.answer("⚠️ Описание товара не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(product_description=description)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer("Введите цену товара в рублях (или /cancel для отмены):")


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: Message, state: FSMContext):
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return
    
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (положительное число). Попробуйте еще раз:")
        return
    
    await state.update_data(product_price=price)
    
    categories = await db.get_categories()
    text = "Выберите категорию для товара:\n\n"
    for cat in categories:
        text += f"ID: {cat['id']} — {cat['name']}\n"
    text += "\nВведите ID категории (или /cancel для отмены):"
    
    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(text)


@router.message(AdminStates.waiting_product_category)
async def add_product_category(message: Message, state: FSMContext):
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление товара отменено.", reply_markup=admin_menu())
        return
    
    try:
        category_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Введите корректный ID категории (число). Попробуйте еще раз:")
        return
    
    categories = await db.get_categories()
    if not any(cat['id'] == category_id for cat in categories):
        await message.answer("❌ Категория с таким ID не найдена. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    
    try:
        await db.db.execute(
            "INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)",
            (category_id, data['product_name'], data['product_description'], data['product_price'])
        )
        await db.db.commit()
        await state.clear()
        await message.answer(
            f"✅ Товар «{data['product_name']}» успешно добавлен!",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"❌ Ошибка при добавлении товара: {e}", reply_markup=admin_menu())


@router.message(F.text == '📦 Товары')
async def show_products_for_delete(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    products = await db.get_products()
    if not products:
        await message.answer("📭 В базе нет товаров.", reply_markup=admin_menu())
        return
    
    await message.answer(
        "📦 Список товаров. Нажмите на товар для удаления:",
        reply_markup=delete_product_buttons(products)
    )


@router.callback_query(F.data.startswith('delete_product:'))
async def delete_product(callback: CallbackQuery):
    await callback.answer()
    
    if not is_admin(callback.from_user.id):
        await callback.message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    try:
        product_id = int(callback.data.split(':')[1])
        await db.delete_product(product_id)
        
        products = await db.get_products()
        if products:
            try:
                await callback.message.edit_text(
                    "✅ Товар удален!\n\n📦 Список товаров. Нажмите на товар для удаления:",
                    reply_markup=delete_product_buttons(products)
                )
            except Exception:
                pass
        else:
            try:
                await callback.message.edit_text("✅ Товар удален!\n\n📭 В базе нет товаров.")
            except Exception:
                pass
    except Exception:
        try:
            await callback.message.edit_text("❌ Ошибка при удалении товара.")
        except Exception:
            pass


@router.message(Command('cancel'))
async def cancel_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных операций.")
        return
    
    await state.clear()
    is_admin = message.from_user.id in settings.ADMIN_IDS
    await message.answer("❌ Операция отменена.", reply_markup=main_menu(is_admin))
