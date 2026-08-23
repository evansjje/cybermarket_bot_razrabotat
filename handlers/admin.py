import logging
from typing import Optional, Union

from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from config import settings
from database import Database

# Настройка логирования
logger = logging.getLogger(__name__)

# Роутер для админ-панели
router = Router(name="admin")

# Проверка на админа (фильтр)
def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором."""
    return user_id in settings.ADMIN_IDS


# ==================== FSM Состояния ====================
class AdminStates(StatesGroup):
    """Состояния для админ-панели."""
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()
    waiting_for_product_file_id = State()
    waiting_for_product_link = State()
    waiting_for_edit_product_id = State()
    waiting_for_edit_field = State()
    waiting_for_edit_value = State()
    waiting_for_delete_product_id = State()


# ==================== Вспомогательные функции ====================
async def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура главного меню админа."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить товар")],
            [KeyboardButton(text="📝 Редактировать товар")],
            [KeyboardButton(text="🗑 Удалить товар")],
            [KeyboardButton(text="📦 Список товаров")],
            [KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Назад в меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard


def get_admin_cancel_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для отмены действия."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ]
    )


def get_product_edit_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора поля для редактирования."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data=f"edit_field:{product_id}:name")],
            [InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_field:{product_id}:description")],
            [InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_field:{product_id}:price")],
            [InlineKeyboardButton(text="📂 Категория", callback_data=f"edit_field:{product_id}:category")],
            [InlineKeyboardButton(text="📎 Файл", callback_data=f"edit_field:{product_id}:file_id")],
            [InlineKeyboardButton(text="🔗 Ссылка", callback_data=f"edit_field:{product_id}:link")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")],
        ]
    )


async def format_product_info(product: dict) -> str:
    """Форматирование информации о товаре для отображения."""
    return (
        f"📦 <b>ID:</b> {product['id']}\n"
        f"📝 <b>Название:</b> {product['name']}\n"
        f"📄 <b>Описание:</b> {product['description']}\n"
        f"💰 <b>Цена:</b> {product['price']} руб.\n"
        f"📂 <b>Категория:</b> {product['category']}\n"
        f"📎 <b>Файл:</b> {'✅ Есть' if product['file_id'] else '❌ Нет'}\n"
        f"🔗 <b>Ссылка:</b> {'✅ Есть' if product['link'] else '❌ Нет'}"
    )


# ==================== Обработчики команд ====================
@router.message(Command("admin"))
async def admin_command(message: Message):
    """Вход в админ-панель по команде /admin."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "👋 Добро пожаловать в админ-панель!\n"
        "Выберите действие:",
        reply_markup=await get_admin_main_keyboard()
    )


@router.message(F.text == "🔙 Назад в меню")
async def back_to_main_menu(message: Message):
    """Возврат в главное меню."""
    if not is_admin(message.from_user.id):
        return

    from keyboards import get_main_keyboard
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "➕ Добавить товар")
async def add_product_start(message: Message, state: FSMContext):
    """Начало добавления товара."""
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_product_name)
    await message.answer(
        "📝 Введите название товара:",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_product_name))
async def add_product_name(message: Message, state: FSMContext):
    """Получение названия товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=await get_admin_main_keyboard())
        return

    await state.update_data(name=message.text)
    await state.set_state(AdminStates.waiting_for_product_description)
    await message.answer(
        "📄 Введите описание товара:",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_product_description))
async def add_product_description(message: Message, state: FSMContext):
    """Получение описания товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=await get_admin_main_keyboard())
        return

    await state.update_data(description=message.text)
    await state.set_state(AdminStates.waiting_for_product_price)
    await message.answer(
        "💰 Введите цену товара (в рублях):",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_product_price))
async def add_product_price(message: Message, state: FSMContext):
    """Получение цены товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=await get_admin_main_keyboard())
        return

    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректную цену (положительное число).")
        return

    await state.update_data(price=price)
    await state.set_state(AdminStates.waiting_for_product_category)
    await message.answer(
        "📂 Введите категорию товара (например: скрипты, софт, мануалы):",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_product_category))
async def add_product_category(message: Message, state: FSMContext):
    """Получение категории товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=await get_admin_main_keyboard())
        return

    await state.update_data(category=message.text)
    await state.set_state(AdminStates.waiting_for_product_file_id)
    await message.answer(
        "📎 Отправьте файл товара (или введите 'пропустить'):",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_product_file_id))
async def add_product_file(message: Message, state: FSMContext, bot: Bot):
    """Получение файла товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=await get_admin_main_keyboard())
        return

    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.lower() == "пропустить":
        pass
    else:
        await message.answer("⚠️ Отправьте файл или введите 'пропустить'.")
        return

    await state.update_data(file_id=file_id)
    await state.set_state(AdminStates.waiting_for_product_link)
    await message.answer(
        "🔗 Введите ссылку на товар (или введите 'пропустить'):",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_product_link))
async def add_product_link(message: Message, state: FSMContext, db: Database):
    """Получение ссылки и сохранение товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено.", reply_markup=await get_admin_main_keyboard())
        return

    link = None
    if message.text and message.text.lower() != "пропустить":
        link = message.text

    data = await state.get_data()
    product_data = {
        "name": data.get("name"),
        "description": data.get("description"),
        "price": data.get("price"),
        "category": data.get("category"),
        "file_id": data.get("file_id"),
        "link": link,
    }

    try:
        product_id = await db.add_product(product_data)
        await state.clear()
        await message.answer(
            f"✅ Товар успешно добавлен!\n"
            f"ID товара: {product_id}\n"
            f"Название: {product_data['name']}\n"
            f"Цена: {product_data['price']} руб.",
            reply_markup=await get_admin_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        await message.answer(
            "❌ Произошла ошибка при добавлении товара. Попробуйте еще раз.",
            reply_markup=await get_admin_main_keyboard()
        )


@router.message(F.text == "📝 Редактировать товар")
async def edit_product_start(message: Message, state: FSMContext):
    """Начало редактирования товара."""
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_edit_product_id)
    await message.answer(
        "📝 Введите ID товара для редактирования:",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_edit_product_id))
async def edit_product_get_id(message: Message, state: FSMContext, db: Database):
    """Получение ID товара для редактирования."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено.", reply_markup=await get_admin_main_keyboard())
        return

    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer("⚠️ Введите корректный ID товара (число).")
        return

    product = await db.get_product(product_id)
    if not product:
        await message.answer("❌ Товар с таким ID не найден.")
        return

    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_for_edit_field)

    await message.answer(
        f"📦 Найден товар:\n\n{await format_product_info(product)}\n\n"
        f"Выберите поле для редактирования:",
        reply_markup=get_product_edit_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("edit_field:"))
async def edit_product_field(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    _, product_id, field = callback.data.split(":")
    await state.update_data(edit_field=field)
    await state.set_state(AdminStates.waiting_for_edit_value)

    field_names = {
        "name": "название",
        "description": "описание",
        "price": "цену",
        "category": "категорию",
        "file_id": "файл",
        "link": "ссылку",
    }

    await callback.message.edit_text(
        f"📝 Введите новое значение для поля '{field_names.get(field, field)}':",
        reply_markup=get_admin_cancel_keyboard()
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.waiting_for_edit_value))
async def edit_product_value(message: Message, state: FSMContext, db: Database):
    """Получение нового значения и обновление товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено.", reply_markup=await get_admin_main_keyboard())
        return

    data = await state.get_data()
    product_id = data.get("product_id")
    field = data.get("edit_field")

    # Для цены проверяем корректность
    if field == "price":
        try:
            value = float(message.text)
            if value <= 0:
                raise ValueError
        except ValueError:
            await message.answer("⚠️ Введите корректную цену (положительное число).")
            return
    else:
        value = message.text

    try:
        await db.update_product(product_id, {field: value})
        await state.clear()
        await message.answer(
            f"✅ Поле '{field}' успешно обновлено!",
            reply_markup=await get_admin_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании товара: {e}")
        await message.answer(
            "❌ Произошла ошибка при редактировании товара.",
            reply_markup=await get_admin_main_keyboard()
        )


@router.message(F.text == "🗑 Удалить товар")
async def delete_product_start(message: Message, state: FSMContext):
    """Начало удаления товара."""
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_delete_product_id)
    await message.answer(
        "🗑 Введите ID товара для удаления:",
        reply_markup=get_admin_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.waiting_for_delete_product_id))
async def delete_product(message: Message, state: FSMContext, db: Database):
    """Удаление товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Удаление отменено.", reply_markup=await get_admin_main_keyboard())
        return

    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer("⚠️ Введите корректный ID товара (число).")
        return

    product = await db.get_product(product_id)
    if not product:
        await message.answer("❌ Товар с таким ID не найден.")
        return

    await db.delete_product(product_id)
    await state.clear()
    await message.answer(
        f"✅ Товар '{product['name']}' (ID: {product_id}) успешно удален!",
        reply_markup=await get_admin_main_keyboard()
    )


@router.message(F.text == "📦 Список товаров")
async def list_products(message: Message, db: Database):
    """Просмотр всех товаров."""
    if not is_admin(message.from_user.id):
        return

    products = await db.get_all_products()
    if not products:
        await message.answer("📦 В базе пока нет товаров.")
        return

    text = "📦 <b>Список всех товаров:</b>\n\n"
    for product in products:
        text += await format_product_info(product) + "\n\n"

    # Разбиваем на части, если сообщение слишком длинное
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000])
    else:
        await message.answer(text)


@router.message(F.text == "👥 Пользователи")
async def list_users(message: Message, db: Database):
    """Просмотр всех пользователей."""
    if not is_admin(message.from_user.id):
        return

    users = await db.get_all_users()
    if not users:
        await message.answer("👥 В базе пока нет пользователей.")
        return

    text = "👥 <b>Список пользователей:</b>\n\n"
    for user in users:
        text += (
            f"ID: {user['id']}\n"
            f"Username: @{user['username'] if user['username'] else 'нет'}\n"
            f"Имя: {user['first_name'] or 'нет'}\n"
            f"Дата регистрации: {user['created_at']}\n"
            f"Реферальный код: {user['referral_code']}\n"
            f"Пригласил: {user['referred_by'] or 'нет'}\n"
            f"Баланс: {user['balance']} руб.\n\n"
        )

    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000])
    else:
        await message.answer(text)


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message, db: Database):
    """Просмотр статистики."""
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_stats()
    if not stats:
        await message.answer("❌ Не удалось получить статистику.")
        return

    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"📦 Всего товаров: {stats['total_products']}\n"
        f"💰 Всего заказов: {stats['total_orders']}\n"
        f"💵 Общая выручка: {stats['total_revenue']} руб.\n"
        f"📈 Средний чек: {stats['avg_order_value']} руб."
    )

    await message.answer(text)


@router.callback_query(F.data == "admin_cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено.",
        reply_markup=None
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=await get_admin_main_keyboard()
    )
    await callback.answer()


# Обработчик для неизвестных команд в админ-панели
@router.message(StateFilter(AdminStates))
async def unknown_admin_action(message: Message):
    """Обработка неизвестных действий в админ-панели."""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⚠️ Неизвестная команда. Используйте кнопки меню или введите /admin для перезапуска."
    )
