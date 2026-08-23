# handlers/admin.py
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from config import settings
from database import Database
from keyboards import main_menu_keyboard

router = Router()
db = Database()

logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()
    waiting_for_product_content = State()
    waiting_for_edit_product_id = State()
    waiting_for_edit_field = State()
    waiting_for_edit_value = State()
    waiting_for_delete_product_id = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in settings.admin_ids_list


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:add_product")
            ],
            [
                InlineKeyboardButton(text="📝 Редактировать товар", callback_data="admin:edit_product")
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin:delete_product")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")
            ],
            [
                InlineKeyboardButton(text="📦 Список товаров", callback_data="admin:list_products")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


def admin_edit_product_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора поля для редактирования"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Название", callback_data="admin:edit_name")
            ],
            [
                InlineKeyboardButton(text="📄 Описание", callback_data="admin:edit_description")
            ],
            [
                InlineKeyboardButton(text="💰 Цена", callback_data="admin:edit_price")
            ],
            [
                InlineKeyboardButton(text="📂 Категория", callback_data="admin:edit_category")
            ],
            [
                InlineKeyboardButton(text="📎 Контент", callback_data="admin:edit_content")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin:panel")
            ]
        ]
    )
    return keyboard


@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    """Открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🛠 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin:panel")
async def admin_panel_callback(callback: CallbackQuery):
    """Открыть админ-панель через callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🛠 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ Добавление нового товара\n\n"
        "Введите название товара:"
    )
    await state.set_state(AdminStates.waiting_for_product_name)
    await callback.answer()


@router.message(AdminStates.waiting_for_product_name)
async def add_product_name(message: Message, state: FSMContext):
    """Получить название товара"""
    await state.update_data(product_name=message.text)
    await message.answer(
        "📄 Введите описание товара:"
    )
    await state.set_state(AdminStates.waiting_for_product_description)


@router.message(AdminStates.waiting_for_product_description)
async def add_product_description(message: Message, state: FSMContext):
    """Получить описание товара"""
    await state.update_data(product_description=message.text)
    await message.answer(
        "💰 Введите цену товара (в рублях):"
    )
    await state.set_state(AdminStates.waiting_for_product_price)


@router.message(AdminStates.waiting_for_product_price)
async def add_product_price(message: Message, state: FSMContext):
    """Получить цену товара"""
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректная цена. Введите положительное число:")
        return
    
    await state.update_data(product_price=price)
    await message.answer(
        "📂 Введите категорию товара:"
    )
    await state.set_state(AdminStates.waiting_for_product_category)


@router.message(AdminStates.waiting_for_product_category)
async def add_product_category(message: Message, state: FSMContext):
    """Получить категорию товара"""
    await state.update_data(product_category=message.text)
    await message.answer(
        "📎 Введите контент товара (текст, ссылку или путь к файлу):"
    )
    await state.set_state(AdminStates.waiting_for_product_content)


@router.message(AdminStates.waiting_for_product_content)
async def add_product_content(message: Message, state: FSMContext):
    """Получить контент товара и сохранить"""
    data = await state.get_data()
    
    try:
        product_id = await db.add_product(
            name=data["product_name"],
            description=data["product_description"],
            price=data["product_price"],
            category=data["product_category"],
            content=message.text
        )
        
        await message.answer(
            f"✅ Товар успешно добавлен!\n\n"
            f"ID: {product_id}\n"
            f"Название: {data['product_name']}\n"
            f"Описание: {data['product_description']}\n"
            f"Цена: {data['product_price']}₽\n"
            f"Категория: {data['product_category']}",
            reply_markup=admin_panel_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        await message.answer(
            "❌ Ошибка при добавлении товара. Попробуйте ещё раз.",
            reply_markup=admin_panel_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data == "admin:edit_product")
async def edit_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📝 Редактирование товара\n\n"
        "Введите ID товара для редактирования:"
    )
    await state.set_state(AdminStates.waiting_for_edit_product_id)
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_product_id)
async def edit_product_id(message: Message, state: FSMContext):
    """Получить ID товара для редактирования"""
    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer("❌ Некорректный ID. Введите число:")
        return
    
    product = await db.get_product(product_id)
    if not product:
        await message.answer(
            f"❌ Товар с ID {product_id} не найден.",
            reply_markup=admin_panel_keyboard()
        )
        await state.clear()
        return
    
    await state.update_data(edit_product_id=product_id)
    await message.answer(
        f"📦 Товар: {product[1]}\n"
        f"💰 Цена: {product[3]}₽\n"
        f"📂 Категория: {product[4]}\n\n"
        f"Выберите поле для редактирования:",
        reply_markup=admin_edit_product_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_edit_field)


@router.callback_query(F.data.startswith("admin:edit_"))
async def edit_product_field(callback: CallbackQuery, state: FSMContext):
    """Выбрать поле для редактирования"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    field = callback.data.split(":", 1)[1]
    
    if field == "name":
        await callback.message.edit_text("Введите новое название товара:")
        await state.set_state(AdminStates.waiting_for_edit_value)
        await state.update_data(edit_field="name")
    elif field == "description":
        await callback.message.edit_text("Введите новое описание товара:")
        await state.set_state(AdminStates.waiting_for_edit_value)
        await state.update_data(edit_field="description")
    elif field == "price":
        await callback.message.edit_text("Введите новую цену товара:")
        await state.set_state(AdminStates.waiting_for_edit_value)
        await state.update_data(edit_field="price")
    elif field == "category":
        await callback.message.edit_text("Введите новую категорию товара:")
        await state.set_state(AdminStates.waiting_for_edit_value)
        await state.update_data(edit_field="category")
    elif field == "content":
        await callback.message.edit_text("Введите новый контент товара:")
        await state.set_state(AdminStates.waiting_for_edit_value)
        await state.update_data(edit_field="content")
    
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_value)
async def edit_product_value(message: Message, state: FSMContext):
    """Получить новое значение поля"""
    data = await state.get_data()
    product_id = data["edit_product_id"]
    field = data["edit_field"]
    value = message.text
    
    try:
        if field == "price":
            value = float(value.replace(",", "."))
            if value <= 0:
                raise ValueError
        
        await db.update_product(product_id, **{field: value})
        
        product = await db.get_product(product_id)
        await message.answer(
            f"✅ Товар успешно обновлён!\n\n"
            f"ID: {product[0]}\n"
            f"Название: {product[1]}\n"
            f"Описание: {product[2]}\n"
            f"Цена: {product[3]}₽\n"
            f"Категория: {product[4]}",
            reply_markup=admin_panel_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании товара: {e}")
        await message.answer(
            "❌ Ошибка при редактировании товара.",
            reply_markup=admin_panel_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data == "admin:delete_product")
async def delete_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать удаление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🗑 Удаление товара\n\n"
        "Введите ID товара для удаления:"
    )
    await state.set_state(AdminStates.waiting_for_delete_product_id)
    await callback.answer()


@router.message(AdminStates.waiting_for_delete_product_id)
async def delete_product_id(message: Message, state: FSMContext):
    """Получить ID товара для удаления"""
    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer("❌ Некорректный ID. Введите число:")
        return
    
    product = await db.get_product(product_id)
    if not product:
        await message.answer(
            f"❌ Товар с ID {product_id} не найден.",
            reply_markup=admin_panel_keyboard()
        )
        await state.clear()
        return
    
    await db.delete_product(product_id)
    await message.answer(
        f"✅ Товар «{product[1]}» успешно удалён!",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    try:
        users_count = await db.get_users_count()
        products_count = await db.get_products_count()
        orders_count = await db.get_orders_count()
        total_revenue = await db.get_total_revenue()
        
        stats_text = (
            f"📊 Статистика бота\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"📦 Товаров: {products_count}\n"
            f"🛒 Заказов: {orders_count}\n"
            f"💰 Выручка: {total_revenue:.2f}₽"
        )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=admin_panel_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики.",
            reply_markup=admin_panel_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin:list_products")
async def admin_list_products(callback: CallbackQuery):
    """Показать список всех товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    products = await db.get_all_products()
    
    if not products:
        await callback.message.edit_text(
            "📦 Список товаров пуст.",
            reply_markup=admin_panel_keyboard()
        )
        await callback.answer()
        return
    
    products_text = "📦 Список всех товаров:\n\n"
    for product in products:
        products_text += (
            f"ID: {product[0]}\n"
            f"Название: {product[1]}\n"
            f"Цена: {product[3]}₽\n"
            f"Категория: {product[4]}\n"
            f"Статус: {'✅ Активен' if product[6] else '❌ Неактивен'}\n"
            f"{'─' * 20}\n"
        )
    
    await callback.message.edit_text(
        products_text,
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.edit_text(
        "Вы вернулись в главное меню.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()
