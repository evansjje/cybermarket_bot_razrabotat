# handlers/admin.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import main_menu_kb
from config import settings

router = Router()
db = Database()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()
    waiting_product_file_path = State()
    waiting_product_download_link = State()
    waiting_edit_product_name = State()
    waiting_edit_product_description = State()
    waiting_edit_product_price = State()
    waiting_edit_product_category = State()
    waiting_edit_product_file_path = State()
    waiting_edit_product_download_link = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in settings.admin_ids_list


def admin_panel_kb() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📝 Редактировать товар", callback_data="admin_edit_product")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="📦 Список товаров", callback_data="admin_list_products")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    return kb


def admin_products_list_kb(products: list[tuple]) -> InlineKeyboardMarkup:
    """Клавиатура со списком товаров для админа"""
    kb = []
    for product in products:
        product_id, name, price = product[0], product[1], product[2]
        kb.append([InlineKeyboardButton(
            text=f"{name} — {price} ₽",
            callback_data=f"admin_select_{product_id}"
        )])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    kb.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_edit_product_kb(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования конкретного товара"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data=f"admin_edit_name_{product_id}")],
        [InlineKeyboardButton(text="📝 Изменить описание", callback_data=f"admin_edit_desc_{product_id}")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"admin_edit_price_{product_id}")],
        [InlineKeyboardButton(text="📂 Изменить категорию", callback_data=f"admin_edit_cat_{product_id}")],
        [InlineKeyboardButton(text="📎 Изменить файл", callback_data=f"admin_edit_file_{product_id}")],
        [InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data=f"admin_edit_link_{product_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_edit_product")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    return kb


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда /admin для открытия админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Возврат в админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_product_name)
    await callback.message.edit_text(
        "➕ Добавление нового товара\n\n"
        "Введите название товара:"
    )
    await callback.answer()


@router.message(AdminStates.waiting_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    """Получение названия товара"""
    await state.update_data(product_name=message.text)
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer("Введите описание товара:")


@router.message(AdminStates.waiting_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    """Получение описания товара"""
    await state.update_data(product_description=message.text)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer("Введите цену товара (в рублях):")


@router.message(AdminStates.waiting_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получение цены товара"""
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректная цена. Введите положительное число:")
        return
    
    await state.update_data(product_price=price)
    await state.set_state(AdminStates.waiting_product_category)
    await message.answer("Введите категорию товара:")


@router.message(AdminStates.waiting_product_category)
async def admin_add_product_category(message: Message, state: FSMContext):
    """Получение категории товара"""
    await state.update_data(product_category=message.text)
    await state.set_state(AdminStates.waiting_product_file_path)
    await message.answer(
        "Введите путь к файлу товара (или отправьте 'нет', если файла нет):"
    )


@router.message(AdminStates.waiting_product_file_path)
async def admin_add_product_file_path(message: Message, state: FSMContext):
    """Получение пути к файлу товара"""
    file_path = message.text if message.text.lower() != 'нет' else None
    await state.update_data(product_file_path=file_path)
    await state.set_state(AdminStates.waiting_product_download_link)
    await message.answer(
        "Введите ссылку для скачивания (или отправьте 'нет', если ссылки нет):"
    )


@router.message(AdminStates.waiting_product_download_link)
async def admin_add_product_download_link(message: Message, state: FSMContext):
    """Получение ссылки для скачивания и сохранение товара"""
    download_link = message.text if message.text.lower() != 'нет' else None
    data = await state.get_data()
    
    product_id = await db.add_product(
        name=data['product_name'],
        description=data['product_description'],
        price=data['product_price'],
        category=data['product_category'],
        file_path=data['product_file_path'],
        download_link=download_link
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Товар успешно добавлен!\n\n"
        f"ID: {product_id}\n"
        f"Название: {data['product_name']}\n"
        f"Цена: {data['product_price']} ₽\n"
        f"Категория: {data['product_category']}",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data == "admin_edit_product")
async def admin_edit_product_start(callback: CallbackQuery):
    """Начало редактирования товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    products = await db.get_all_products()
    if not products:
        await callback.message.edit_text(
            "📦 Список товаров пуст.",
            reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📝 Выберите товар для редактирования:",
        reply_markup=admin_products_list_kb(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_select_"))
async def admin_select_product(callback: CallbackQuery):
    """Выбор товара для редактирования"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    product_id = int(callback.data.replace("admin_select_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return
    
    product_id, name, description, price, category, file_path, download_link, is_available = product
    
    text = (
        f"📦 Товар #{product_id}\n\n"
        f"📝 Название: {name}\n"
        f"📄 Описание: {description}\n"
        f"💰 Цена: {price} ₽\n"
        f"📂 Категория: {category}\n"
        f"📎 Файл: {file_path or 'Нет'}\n"
        f"🔗 Ссылка: {download_link or 'Нет'}\n"
        f"📊 Доступен: {'Да' if is_available else 'Нет'}\n\n"
        f"Выберите поле для редактирования:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_edit_product_kb(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_name_"))
async def admin_edit_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия"""
    product_id = int(callback.data.replace("admin_edit_name_", ""))
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_name)
    await callback.message.edit_text("Введите новое название товара:")
    await callback.answer()


@router.message(AdminStates.waiting_edit_product_name)
async def admin_edit_name(message: Message, state: FSMContext):
    """Сохранение нового названия"""
    data = await state.get_data()
    product_id = data['edit_product_id']
    
    await db.update_product(product_id, name=message.text)
    await state.clear()
    
    product = await db.get_product(product_id)
    await message.answer(
        f"✅ Название обновлено!\n\n"
        f"Товар: {product[1]}\n"
        f"Цена: {product[3]} ₽",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data.startswith("admin_edit_desc_"))
async def admin_edit_desc_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания"""
    product_id = int(callback.data.replace("admin_edit_desc_", ""))
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_description)
    await callback.message.edit_text("Введите новое описание товара:")
    await callback.answer()


@router.message(AdminStates.waiting_edit_product_description)
async def admin_edit_desc(message: Message, state: FSMContext):
    """Сохранение нового описания"""
    data = await state.get_data()
    product_id = data['edit_product_id']
    
    await db.update_product(product_id, description=message.text)
    await state.clear()
    
    product = await db.get_product(product_id)
    await message.answer(
        f"✅ Описание обновлено!\n\n"
        f"Товар: {product[1]}\n"
        f"Описание: {product[2]}",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data.startswith("admin_edit_price_"))
async def admin_edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""
    product_id = int(callback.data.replace("admin_edit_price_", ""))
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_price)
    await callback.message.edit_text("Введите новую цену товара:")
    await callback.answer()


@router.message(AdminStates.waiting_edit_product_price)
async def admin_edit_price(message: Message, state: FSMContext):
    """Сохранение новой цены"""
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректная цена. Введите положительное число:")
        return
    
    data = await state.get_data()
    product_id = data['edit_product_id']
    
    await db.update_product(product_id, price=price)
    await state.clear()
    
    product = await db.get_product(product_id)
    await message.answer(
        f"✅ Цена обновлена!\n\n"
        f"Товар: {product[1]}\n"
        f"Цена: {product[3]} ₽",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data.startswith("admin_edit_cat_"))
async def admin_edit_cat_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования категории"""
    product_id = int(callback.data.replace("admin_edit_cat_", ""))
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_category)
    await callback.message.edit_text("Введите новую категорию товара:")
    await callback.answer()


@router.message(AdminStates.waiting_edit_product_category)
async def admin_edit_cat(message: Message, state: FSMContext):
    """Сохранение новой категории"""
    data = await state.get_data()
    product_id = data['edit_product_id']
    
    await db.update_product(product_id, category=message.text)
    await state.clear()
    
    product = await db.get_product(product_id)
    await message.answer(
        f"✅ Категория обновлена!\n\n"
        f"Товар: {product[1]}\n"
        f"Категория: {product[4]}",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data.startswith("admin_edit_file_"))
async def admin_edit_file_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования файла"""
    product_id = int(callback.data.replace("admin_edit_file_", ""))
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_file_path)
    await callback.message.edit_text("Введите новый путь к файлу (или 'нет' для удаления):")
    await callback.answer()


@router.message(AdminStates.waiting_edit_product_file_path)
async def admin_edit_file(message: Message, state: FSMContext):
    """Сохранение нового пути к файлу"""
    data = await state.get_data()
    product_id = data['edit_product_id']
    
    file_path = message.text if message.text.lower() != 'нет' else None
    await db.update_product(product_id, file_path=file_path)
    await state.clear()
    
    product = await db.get_product(product_id)
    await message.answer(
        f"✅ Файл обновлен!\n\n"
        f"Товар: {product[1]}\n"
        f"Файл: {product[5] or 'Нет'}",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data.startswith("admin_edit_link_"))
async def admin_edit_link_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования ссылки"""
    product_id = int(callback.data.replace("admin_edit_link_", ""))
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_download_link)
    await callback.message.edit_text("Введите новую ссылку для скачивания (или 'нет' для удаления):")
    await callback.answer()


@router.message(AdminStates.waiting_edit_product_download_link)
async def admin_edit_link(message: Message, state: FSMContext):
    """Сохранение новой ссылки"""
    data = await state.get_data()
    product_id = data['edit_product_id']
    
    download_link = message.text if message.text.lower() != 'нет' else None
    await db.update_product(product_id, download_link=download_link)
    await state.clear()
    
    product = await db.get_product(product_id)
    await message.answer(
        f"✅ Ссылка обновлена!\n\n"
        f"Товар: {product[1]}\n"
        f"Ссылка: {product[6] or 'Нет'}",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product_start(callback: CallbackQuery):
    """Начало удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    products = await db.get_all_products()
    if not products:
        await callback.message.edit_text(
            "📦 Список товаров пуст.",
            reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return
    
    kb = []
    for product in products:
        product_id, name, price = product[0], product[1], product[2]
        kb.append([InlineKeyboardButton(
            text=f"🗑 {name} — {price} ₽",
            callback_data=f"admin_confirm_delete_{product_id}"
        )])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    kb.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    await callback.message.edit_text(
        "🗑 Выберите товар для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def admin_confirm_delete(callback: CallbackQuery):
    """Подтверждение удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    product_id = int(callback.data.replace("admin_confirm_delete_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден.",
            reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return
    
    await db.delete_product(product_id)
    
    await callback.message.edit_text(
        f"✅ Товар «{product[1]}» успешно удален!",
        reply_markup=admin_panel_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_list_products")
async def admin_list_products(callback: CallbackQuery):
    """Просмотр всех товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    products = await db.get_all_products()
    if not products:
        await callback.message.edit_text(
            "📦 Список товаров пуст.",
            reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return
    
    text = "📦 Все товары:\n\n"
    for product in products:
        product_id, name, description, price, category, file_path, download_link, is_available = product
        text += (
            f"#{product_id} | {name}\n"
            f"💰 {price} ₽ | 📂 {category}\n"
            f"📊 {'✅ Доступен' if is_available else '❌ Недоступен'}\n"
            f"━━━━━━━━━━━━━\n"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_kb()
    )
    await callback.answer()
