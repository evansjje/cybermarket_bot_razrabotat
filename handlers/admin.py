from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from database import Database
from config import settings
from keyboards import main_menu_keyboard
from typing import Optional, List, Dict, Any
import logging

router = Router()
logger = logging.getLogger(__name__)

# Состояния для админ-панели
class AdminStates(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()
    waiting_for_product_file = State()
    waiting_for_product_link = State()
    waiting_for_edit_product = State()
    waiting_for_edit_field = State()
    waiting_for_edit_value = State()

# Вспомогательная функция для проверки прав администратора
def is_admin(user_id: int) -> bool:
    return settings.is_admin(user_id)

@router.message(Command("admin"))
async def admin_panel(message: Message, db: Database):
    """Открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:add_product")],
        [InlineKeyboardButton(text="📝 Редактировать товар", callback_data="admin:edit_product")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin:delete_product")],
        [InlineKeyboardButton(text="📦 Список товаров", callback_data="admin:list_products")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:list_users")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await message.answer("🛠 Админ-панель\n\nВыберите действие:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("admin:"))
async def admin_callback(callback: CallbackQuery, db: Database, state: FSMContext):
    """Обработка callback-запросов из админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    action = callback.data.split(":", 1)[1]
    
    if action == "add_product":
        await state.set_state(AdminStates.waiting_for_product_name)
        await callback.message.edit_text(
            "➕ Добавление нового товара\n\n"
            "Введите название товара:"
        )
    
    elif action == "edit_product":
        products = await db.get_all_products()
        if not products:
            await callback.message.edit_text("📦 Товаров пока нет.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for product in products:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"✏️ {product['name']} — {product['price']}₽",
                    callback_data=f"admin:edit_product:{product['product_id']}"
                )
            ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")])
        
        await callback.message.edit_text("📝 Выберите товар для редактирования:", reply_markup=keyboard)
    
    elif action == "delete_product":
        products = await db.get_all_products()
        if not products:
            await callback.message.edit_text("📦 Товаров пока нет.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for product in products:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🗑 {product['name']} — {product['price']}₽",
                    callback_data=f"admin:delete_product:{product['product_id']}"
                )
            ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")])
        
        await callback.message.edit_text("🗑 Выберите товар для удаления:", reply_markup=keyboard)
    
    elif action == "list_products":
        products = await db.get_all_products()
        if not products:
            await callback.message.edit_text("📦 Товаров пока нет.")
            return
        
        text = "📦 Список товаров:\n\n"
        for product in products:
            text += f"ID: {product['product_id']}\n"
            text += f"Название: {product['name']}\n"
            text += f"Цена: {product['price']}₽\n"
            text += f"Категория: {product['category']}\n"
            text += f"Доступен: {'✅' if product['is_available'] else '❌'}\n"
            text += "─" * 20 + "\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    elif action == "list_users":
        users = await db.get_all_users()
        if not users:
            await callback.message.edit_text("👥 Пользователей пока нет.")
            return
        
        text = "👥 Список пользователей:\n\n"
        for user in users:
            text += f"ID: {user['user_id']}\n"
            text += f"Username: @{user['username'] if user['username'] else 'нет'}\n"
            text += f"Имя: {user['first_name']}\n"
            text += f"Дата регистрации: {user['registration_date']}\n"
            text += f"Баланс: {user['balance']}₽\n"
            text += "─" * 20 + "\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    elif action == "stats":
        stats = await db.get_stats()
        text = "📊 Статистика бота:\n\n"
        text += f"👥 Пользователей: {stats['total_users']}\n"
        text += f"📦 Товаров: {stats['total_products']}\n"
        text += f"🛒 Заказов: {stats['total_orders']}\n"
        text += f"💰 Выручка: {stats['total_revenue']}₽\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    elif action == "back":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:add_product")],
            [InlineKeyboardButton(text="📝 Редактировать товар", callback_data="admin:edit_product")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin:delete_product")],
            [InlineKeyboardButton(text="📦 Список товаров", callback_data="admin:list_products")],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:list_users")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text("🛠 Админ-панель\n\nВыберите действие:", reply_markup=keyboard)
    
    elif action.startswith("edit_product:"):
        product_id = int(action.split(":")[1])
        product = await db.get_product(product_id)
        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return
        
        await state.update_data(edit_product_id=product_id)
        await state.set_state(AdminStates.waiting_for_edit_field)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Название", callback_data="admin:edit_field:name")],
            [InlineKeyboardButton(text="Описание", callback_data="admin:edit_field:description")],
            [InlineKeyboardButton(text="Цена", callback_data="admin:edit_field:price")],
            [InlineKeyboardButton(text="Категория", callback_data="admin:edit_field:category")],
            [InlineKeyboardButton(text="Файл", callback_data="admin:edit_field:file_path")],
            [InlineKeyboardButton(text="Ссылка", callback_data="admin:edit_field:download_link")],
            [InlineKeyboardButton(text="Доступность", callback_data="admin:edit_field:is_available")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")]
        ])
        
        await callback.message.edit_text(
            f"📝 Редактирование товара:\n\n"
            f"ID: {product['product_id']}\n"
            f"Название: {product['name']}\n"
            f"Описание: {product['description']}\n"
            f"Цена: {product['price']}₽\n"
            f"Категория: {product['category']}\n"
            f"Файл: {product['file_path']}\n"
            f"Ссылка: {product['download_link']}\n"
            f"Доступен: {'✅' if product['is_available'] else '❌'}\n\n"
            f"Выберите поле для редактирования:",
            reply_markup=keyboard
        )
    
    elif action.startswith("edit_field:"):
        field = action.split(":")[1]
        await state.update_data(edit_field=field)
        
        field_names = {
            "name": "название",
            "description": "описание",
            "price": "цену",
            "category": "категорию",
            "file_path": "путь к файлу",
            "download_link": "ссылку для скачивания",
            "is_available": "доступность (1/0)"
        }
        
        await state.set_state(AdminStates.waiting_for_edit_value)
        await callback.message.edit_text(f"Введите новое значение для поля «{field_names.get(field, field)}»:")
    
    elif action.startswith("delete_product:"):
        product_id = int(action.split(":")[1])
        await db.delete_product(product_id)
        await callback.answer("✅ Товар удален", show_alert=True)
        
        # Показываем обновленный список
        products = await db.get_all_products()
        if not products:
            await callback.message.edit_text("📦 Товаров пока нет.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for product in products:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🗑 {product['name']} — {product['price']}₽",
                    callback_data=f"admin:delete_product:{product['product_id']}"
                )
            ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")])
        
        await callback.message.edit_text("🗑 Выберите товар для удаления:", reply_markup=keyboard)

@router.message(AdminStates.waiting_for_product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка названия товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа")
        return
    
    await state.update_data(product_name=message.text)
    await state.set_state(AdminStates.waiting_for_product_description)
    await message.answer("Введите описание товара:")

@router.message(AdminStates.waiting_for_product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка описания товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа")
        return
    
    await state.update_data(product_description=message.text)
    await state.set_state(AdminStates.waiting_for_product_price)
    await message.answer("Введите цену товара (в рублях):")

@router.message(AdminStates.waiting_for_product_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа")
        return
    
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректная цена. Введите положительное число:")
        return
    
    await state.update_data(product_price=price)
    await state.set_state(AdminStates.waiting_for_product_category)
    await message.answer("Введите категорию товара:")

@router.message(AdminStates.waiting_for_product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обработка категории товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа")
        return
    
    await state.update_data(product_category=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 Отправить файл", callback_data="admin:send_file")],
        [InlineKeyboardButton(text="🔗 Указать ссылку", callback_data="admin:send_link")],
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="admin:skip_file")]
    ])
    
    await state.set_state(AdminStates.waiting_for_product_file)
    await message.answer("Выберите способ предоставления товара:", reply_markup=keyboard)

@router.callback_query(F.data == "admin:send_file")
async def process_send_file(callback: CallbackQuery, state: FSMContext):
    """Запрос файла товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа")
        return
    
    await state.set_state(AdminStates.waiting_for_product_file)
    await callback.message.edit_text("📎 Отправьте файл товара:")

@router.callback_query(F.data == "admin:send_link")
async def process_send_link(callback: CallbackQuery, state: FSMContext):
    """Запрос ссылки товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа")
        return
    
    await state.set_state(AdminStates.waiting_for_product_link)
    await callback.message.edit_text("🔗 Введите ссылку для скачивания товара:")

@router.callback_query(F.data == "admin:skip_file")
async def process_skip_file(callback: CallbackQuery, state: FSMContext, db: Database):
    """Пропустить файл и сохранить товар"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа")
        return
    
    data = await state.get_data()
    await db.create_product(
        name=data["product_name"],
        description=data["product_description"],
        price=data["product_price"],
        category=data["product_category"],
        file_path=None,
        download_link=None
    )
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ Товар успешно добавлен!\n\n"
        f"Название: {data['product_name']}\n"
        f"Описание: {data['product_description']}\n"
        f"Цена: {data['product_price']}₽\n"
        f"Категория: {data['product_category']}"
    )

@router.message(AdminStates.waiting_for_product_file)
async def process_product_file(message: Message, state: FSMContext, db: Database):
    """Обработка файла товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа")
        return
    
    if not message.document:
        await message.answer("❌ Пожалуйста, отправьте файл:")
        return
    
    # Сохраняем файл
    file = message.document
    file_path = f"downloads/{file.file_id}_{file.file_name}"
    
    # Создаем директорию, если её нет
    import os
    os.makedirs("downloads", exist_ok=True)
    
    # Скачиваем файл
    destination = await message.bot.download(file)
    with open(file_path, "wb") as f:
        f.write(destination.read())
    
    data = await state.get_data()
    await db.create_product(
        name=data["product_name"],
        description=data["product_description"],
        price=data["product_price"],
        category=data["product_category"],
        file_path=file_path,
        download_link=None
    )
    
    await state.clear()
    await message.answer(
        f"✅ Товар успешно добавлен!\n\n"
        f"Название: {data['product_name']}\n"
        f"Описание: {data['product_description']}\n"
        f"Цена: {data['product_price']}₽\n"
        f"Категория: {data['product_category']}\n"
        f"Файл: {file.file_name}"
    )

@router.message(AdminStates.waiting_for_product_link)
async def process_product_link(message: Message, state: FSMContext, db: Database):
    """Обработка ссылки товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа")
        return
    
    data = await state.get_data()
    await db.create_product(
        name=data["product_name"],
        description=data["product_description"],
        price=data["product_price"],
        category=data["product_category"],
        file_path=None,
        download_link=message.text
    )
    
    await state.clear()
    await message.answer(
        f"✅ Товар успешно добавлен!\n\n"
        f"Название: {data['product_name']}\n"
        f"Описание: {data['product_description']}\n"
        f"Цена: {data['product_price']}₽\n"
        f"Категория: {data['product_category']}\n"
        f"Ссылка: {message.text}"
    )

@router.message(AdminStates.waiting_for_edit_value)
async def process_edit_value(message: Message, state: FSMContext, db: Database):
    """Обработка нового значения для редактирования"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Нет доступа")
        return
    
    data = await state.get_data()
    product_id = data["edit_product_id"]
    field = data["edit_field"]
    
    # Преобразуем значение для поля is_available
    if field == "is_available":
        value = 1 if message.text.lower() in ["1", "да", "yes", "true"] else 0
    elif field == "price":
        try:
            value = float(message.text.replace(",", "."))
        except ValueError:
            await message.answer("❌ Некорректная цена. Введите число:")
            return
    else:
        value = message.text
    
    await db.update_product(product_id, **{field: value})
    await state.clear()
    
    product = await db.get_product(product_id)
    await message.answer(
        f"✅ Товар обновлен!\n\n"
        f"ID: {product['product_id']}\n"
        f"Название: {product['name']}\n"
        f"Описание: {product['description']}\n"
        f"Цена: {product['price']}₽\n"
        f"Категория: {product['category']}\n"
        f"Файл: {product['file_path']}\n"
        f"Ссылка: {product['download_link']}\n"
        f"Доступен: {'✅' if product['is_available'] else '❌'}"
    )
