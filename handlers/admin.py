import logging
from typing import List, Optional, Dict, Any

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter

from config import settings
from database import db
from keyboards import (
    get_main_menu,
    get_admin_panel_keyboard,
    get_admin_products_keyboard,
    get_admin_product_actions_keyboard,
    get_admin_confirm_keyboard,
    get_admin_categories_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    """Состояния для админ-панели."""
    admin_menu = State()
    adding_product_name = State()
    adding_product_description = State()
    adding_product_price = State()
    adding_product_category = State()
    adding_product_file_id = State()
    adding_product_file_path = State()
    editing_product_name = State()
    editing_product_description = State()
    editing_product_price = State()
    editing_product_category = State()
    editing_product_file_id = State()
    editing_product_file_path = State()
    deleting_product_confirm = State()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in settings.admin_ids_list


@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    """Команда /admin для входа в админ-панель."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await message.answer(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_panel_keyboard()
    )


@router.message(F.text == "👨‍💻 Админ-панель")
async def admin_panel_button(message: Message, state: FSMContext):
    """Кнопка админ-панели в главном меню."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await message.answer(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin_panel", StateFilter(AdminStates.admin_menu))
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ-панель."""
    await callback.message.edit_text(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_product", StateFilter(AdminStates.admin_menu))
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара."""
    await state.set_state(AdminStates.adding_product_name)
    await callback.message.edit_text(
        "➕ Добавление нового товара\n\n"
        "Введите название товара:"
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.adding_product_name))
async def admin_add_product_name(message: Message, state: FSMContext):
    """Получение названия товара."""
    if not message.text or len(message.text) > 100:
        await message.answer("❌ Название товара должно быть не длиннее 100 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(product_name=message.text)
    await state.set_state(AdminStates.adding_product_description)
    await message.answer("Введите описание товара:")


@router.message(StateFilter(AdminStates.adding_product_description))
async def admin_add_product_description(message: Message, state: FSMContext):
    """Получение описания товара."""
    if not message.text or len(message.text) > 1000:
        await message.answer("❌ Описание товара должно быть не длиннее 1000 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(product_description=message.text)
    await state.set_state(AdminStates.adding_product_price)
    await message.answer("Введите цену товара (в рублях, число):")


@router.message(StateFilter(AdminStates.adding_product_price))
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получение цены товара."""
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Цена должна быть положительным числом. Попробуйте еще раз:")
        return
    
    await state.update_data(product_price=price)
    
    # Получаем список категорий для выбора
    categories = await db.get_categories()
    if not categories:
        # Если категорий нет, создаем категорию "Общее"
        await db.add_category("Общее")
        categories = ["Общее"]
    
    await state.set_state(AdminStates.adding_product_category)
    await message.answer(
        "Выберите категорию товара:",
        reply_markup=get_admin_categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith("admin_category:"), StateFilter(AdminStates.adding_product_category))
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории товара."""
    category = callback.data.split(":", 1)[1]
    await state.update_data(product_category=category)
    await state.set_state(AdminStates.adding_product_file_id)
    await callback.message.edit_text(
        "📎 Отправьте файл товара (или введите file_id):\n\n"
        "Можно отправить файл напрямую или ввести его file_id."
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.adding_product_file_id))
async def admin_add_product_file(message: Message, state: FSMContext):
    """Получение файла товара."""
    file_id = None
    file_path = None
    
    if message.document:
        file_id = message.document.file_id
        file_path = f"{settings.PRODUCTS_DIR}/{message.document.file_name}"
    elif message.text:
        file_id = message.text.strip()
        file_path = f"{settings.PRODUCTS_DIR}/product_{file_id[:10]}.dat"
    else:
        await message.answer("❌ Пожалуйста, отправьте файл или введите file_id:")
        return
    
    await state.update_data(product_file_id=file_id, product_file_path=file_path)
    
    # Сохраняем товар в базу данных
    data = await state.get_data()
    try:
        product_id = await db.add_product(
            name=data["product_name"],
            description=data["product_description"],
            price=data["product_price"],
            category=data["product_category"],
            file_id=file_id,
            file_path=file_path
        )
        
        await state.clear()
        await state.set_state(AdminStates.admin_menu)
        await message.answer(
            f"✅ Товар успешно добавлен!\n\n"
            f"📦 Название: {data['product_name']}\n"
            f"💰 Цена: {data['product_price']}₽\n"
            f"📂 Категория: {data['product_category']}\n"
            f"🆔 ID товара: {product_id}",
            reply_markup=get_admin_panel_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка добавления товара: {e}")
        await message.answer("❌ Произошла ошибка при добавлении товара. Попробуйте еще раз.")
        await state.clear()
        await state.set_state(AdminStates.admin_menu)
        await message.answer(
            "👨‍💻 Админ-панель",
            reply_markup=get_admin_panel_keyboard()
        )


@router.callback_query(F.data == "admin_list_products", StateFilter(AdminStates.admin_menu))
async def admin_list_products(callback: CallbackQuery, state: FSMContext):
    """Просмотр списка товаров."""
    products = await db.get_all_products()
    
    if not products:
        await callback.message.edit_text(
            "📭 Список товаров пуст.\n\n"
            "Добавьте первый товар!",
            reply_markup=get_admin_panel_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📦 Список товаров:\n\n"
        "Выберите товар для управления:",
        reply_markup=get_admin_products_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product:"), StateFilter(AdminStates.admin_menu))
async def admin_product_actions(callback: CallbackQuery, state: FSMContext):
    """Действия с выбранным товаром."""
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    await state.update_data(editing_product_id=product_id)
    
    await callback.message.edit_text(
        f"📦 Товар: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📂 Категория: {product['category']}\n"
        f"📝 Описание: {product['description'][:100]}...\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_name:"), StateFilter(AdminStates.admin_menu))
async def admin_edit_product_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия."""
    await state.set_state(AdminStates.editing_product_name)
    await callback.message.edit_text(
        "✏️ Введите новое название товара:"
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_product_name))
async def admin_edit_product_name(message: Message, state: FSMContext):
    """Получение нового названия."""
    if not message.text or len(message.text) > 100:
        await message.answer("❌ Название товара должно быть не длиннее 100 символов. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    try:
        await db.update_product(product_id, name=message.text)
        await message.answer("✅ Название товара обновлено!")
    except Exception as e:
        logger.error(f"Ошибка обновления названия: {e}")
        await message.answer("❌ Ошибка при обновлении названия.")
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await message.answer(
        "👨‍💻 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data.startswith("admin_edit_description:"), StateFilter(AdminStates.admin_menu))
async def admin_edit_product_description_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания."""
    await state.set_state(AdminStates.editing_product_description)
    await callback.message.edit_text(
        "✏️ Введите новое описание товара:"
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_product_description))
async def admin_edit_product_description(message: Message, state: FSMContext):
    """Получение нового описания."""
    if not message.text or len(message.text) > 1000:
        await message.answer("❌ Описание товара должно быть не длиннее 1000 символов. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    try:
        await db.update_product(product_id, description=message.text)
        await message.answer("✅ Описание товара обновлено!")
    except Exception as e:
        logger.error(f"Ошибка обновления описания: {e}")
        await message.answer("❌ Ошибка при обновлении описания.")
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await message.answer(
        "👨‍💻 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data.startswith("admin_edit_price:"), StateFilter(AdminStates.admin_menu))
async def admin_edit_product_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены."""
    await state.set_state(AdminStates.editing_product_price)
    await callback.message.edit_text(
        "✏️ Введите новую цену товара (в рублях):"
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_product_price))
async def admin_edit_product_price(message: Message, state: FSMContext):
    """Получение новой цены."""
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Цена должна быть положительным числом. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    try:
        await db.update_product(product_id, price=price)
        await message.answer("✅ Цена товара обновлена!")
    except Exception as e:
        logger.error(f"Ошибка обновления цены: {e}")
        await message.answer("❌ Ошибка при обновлении цены.")
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await message.answer(
        "👨‍💻 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data.startswith("admin_edit_category:"), StateFilter(AdminStates.admin_menu))
async def admin_edit_product_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования категории."""
    categories = await db.get_categories()
    if not categories:
        await callback.answer("❌ Нет доступных категорий", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_product_category)
    await callback.message.edit_text(
        "✏️ Выберите новую категорию:",
        reply_markup=get_admin_categories_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_category:"), StateFilter(AdminStates.editing_product_category))
async def admin_edit_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбор новой категории."""
    category = callback.data.split(":", 1)[1]
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    try:
        await db.update_product(product_id, category=category)
        await callback.message.edit_text("✅ Категория товара обновлена!")
    except Exception as e:
        logger.error(f"Ошибка обновления категории: {e}")
        await callback.message.edit_text("❌ Ошибка при обновлении категории.")
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await callback.message.answer(
        "👨‍💻 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_file:"), StateFilter(AdminStates.admin_menu))
async def admin_edit_product_file_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования файла."""
    await state.set_state(AdminStates.editing_product_file_id)
    await callback.message.edit_text(
        "📎 Отправьте новый файл товара (или введите file_id):"
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_product_file_id))
async def admin_edit_product_file(message: Message, state: FSMContext):
    """Получение нового файла."""
    file_id = None
    file_path = None
    
    if message.document:
        file_id = message.document.file_id
        file_path = f"{settings.PRODUCTS_DIR}/{message.document.file_name}"
    elif message.text:
        file_id = message.text.strip()
        file_path = f"{settings.PRODUCTS_DIR}/product_{file_id[:10]}.dat"
    else:
        await message.answer("❌ Пожалуйста, отправьте файл или введите file_id:")
        return
    
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    try:
        await db.update_product(product_id, file_id=file_id, file_path=file_path)
        await message.answer("✅ Файл товара обновлен!")
    except Exception as e:
        logger.error(f"Ошибка обновления файла: {e}")
        await message.answer("❌ Ошибка при обновлении файла.")
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await message.answer(
        "👨‍💻 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data.startswith("admin_delete:"), StateFilter(AdminStates.admin_menu))
async def admin_delete_product_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара."""
    product_id = int(callback.data.split(":", 1)[1])
    await state.update_data(deleting_product_id=product_id)
    await state.set_state(AdminStates.deleting_product_confirm)
    
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить этот товар?\n"
        "Это действие необратимо!",
        reply_markup=get_admin_confirm_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_confirm_delete", StateFilter(AdminStates.deleting_product_confirm))
async def admin_delete_product(callback: CallbackQuery, state: FSMContext):
    """Удаление товара."""
    data = await state.get_data()
    product_id = data.get("deleting_product_id")
    
    try:
        await db.delete_product(product_id)
        await callback.message.edit_text("✅ Товар успешно удален!")
    except Exception as e:
        logger.error(f"Ошибка удаления товара: {e}")
        await callback.message.edit_text("❌ Ошибка при удалении товара.")
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await callback.message.answer(
        "👨‍💻 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cancel_delete", StateFilter(AdminStates.deleting_product_confirm))
async def admin_cancel_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления."""
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await callback.message.edit_text(
        "👨‍💻 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats", StateFilter(AdminStates.admin_menu))
async def admin_stats(callback: CallbackQuery, state: FSMContext):
    """Просмотр статистики."""
    try:
        users_count = await db.get_users_count()
        products_count = await db.get_products_count()
        orders_count = await db.get_orders_count()
        total_revenue = await db.get_total_revenue()
        
        await callback.message.edit_text(
            f"📊 Статистика бота:\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"📦 Товаров: {products_count}\n"
            f"🛒 Заказов: {orders_count}\n"
            f"💰 Общая выручка: {total_revenue}₽",
            reply_markup=get_admin_panel_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики.",
            reply_markup=get_admin_panel_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "admin_back", StateFilter(AdminStates.admin_menu))
async def admin_back(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=get_main_menu()
    )
    await callback.answer()
