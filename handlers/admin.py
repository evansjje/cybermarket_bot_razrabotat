from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import settings
from database import Database
from keyboards import (
    get_admin_panel_keyboard,
    get_admin_products_keyboard,
    get_admin_product_actions_keyboard,
    get_admin_categories_keyboard,
    get_admin_confirm_keyboard,
    get_admin_edit_keyboard,
    get_main_menu
)

router = Router()
db = Database()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    admin_menu = State()
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()
    waiting_product_file = State()
    waiting_product_link = State()
    waiting_edit_product_name = State()
    waiting_edit_product_description = State()
    waiting_edit_product_price = State()
    waiting_edit_product_category = State()
    waiting_edit_product_file = State()
    waiting_edit_product_link = State()
    waiting_delete_confirm = State()
    waiting_category_name = State()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return settings.is_admin(user_id)


async def get_all_products() -> List[Dict[str, Any]]:
    """Получает все товары из базы данных"""
    if not db.connection:
        await db.connect()
    cursor = await db.connection.execute(
        "SELECT id, name, description, price, category, file_path, download_link, is_active FROM products ORDER BY id DESC"
    )
    rows = await cursor.fetchall()
    products = []
    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "category": row[4],
            "file_path": row[5],
            "download_link": row[6],
            "is_active": row[7]
        })
    return products


async def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Получает товар по ID"""
    if not db.connection:
        await db.connect()
    cursor = await db.connection.execute(
        "SELECT id, name, description, price, category, file_path, download_link, is_active FROM products WHERE id = ?",
        (product_id,)
    )
    row = await cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "category": row[4],
            "file_path": row[5],
            "download_link": row[6],
            "is_active": row[7]
        }
    return None


async def get_all_categories() -> List[str]:
    """Получает все категории товаров"""
    if not db.connection:
        await db.connect()
    cursor = await db.connection.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    """Обработчик команды /admin"""
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


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия на кнопку админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await callback.message.edit_text(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_product_name)
    await callback.message.edit_text(
        "📝 Добавление нового товара\n\n"
        "Введите название товара:"
    )


@router.message(AdminStates.waiting_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    """Получение названия товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    product_name = message.text.strip()
    if len(product_name) < 2:
        await message.answer("❌ Название товара должно быть не короче 2 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer(
        f"✅ Название товара: {product_name}\n\n"
        "Теперь введите описание товара:"
    )


@router.message(AdminStates.waiting_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    """Получение описания товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    product_description = message.text.strip()
    if len(product_description) < 5:
        await message.answer("❌ Описание товара должно быть не короче 5 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(product_description=product_description)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        f"✅ Описание товара: {product_description}\n\n"
        "Теперь введите цену товара (в рублях):"
    )


@router.message(AdminStates.waiting_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получение цены товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число). Попробуйте еще раз:")
        return
    
    await state.update_data(product_price=price)
    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        f"✅ Цена товара: {price}₽\n\n"
        "Теперь введите категорию товара:"
    )


@router.message(AdminStates.waiting_product_category)
async def admin_add_product_category(message: Message, state: FSMContext):
    """Получение категории товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    category = message.text.strip()
    if len(category) < 2:
        await message.answer("❌ Категория должна быть не короче 2 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(product_category=category)
    await state.set_state(AdminStates.waiting_product_file)
    await message.answer(
        f"✅ Категория товара: {category}\n\n"
        "Теперь отправьте файл товара (или введите ссылку на скачивание):"
    )


@router.message(AdminStates.waiting_product_file)
async def admin_add_product_file(message: Message, state: FSMContext):
    """Получение файла или ссылки товара"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    data = await state.get_data()
    file_path = None
    download_link = None
    
    if message.document:
        # Сохраняем файл
        file_info = message.document
        file_path = f"files/products/{file_info.file_unique_id}_{file_info.file_name}"
        
        import os
        os.makedirs("files/products", exist_ok=True)
        
        destination = file_path
        await message.bot.download(file_info, destination)
        
        download_link = None
        await message.answer("✅ Файл получен и сохранен.")
    elif message.text:
        # Ссылка на скачивание
        download_link = message.text.strip()
        if not download_link.startswith(("http://", "https://")):
            await message.answer("❌ Ссылка должна начинаться с http:// или https://. Попробуйте еще раз:")
            return
        await message.answer("✅ Ссылка получена.")
    else:
        await message.answer("❌ Отправьте файл или введите ссылку на скачивание:")
        return
    
    await state.update_data(
        product_file_path=file_path,
        product_download_link=download_link
    )
    
    # Сохраняем товар в базу данных
    if not db.connection:
        await db.connect()
    
    cursor = await db.connection.execute(
        """INSERT INTO products (name, description, price, category, file_path, download_link, is_active)
           VALUES (?, ?, ?, ?, ?, ?, 1)""",
        (
            data["product_name"],
            data["product_description"],
            data["product_price"],
            data["product_category"],
            file_path,
            download_link
        )
    )
    await db.connection.commit()
    product_id = cursor.lastrowid
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    await message.answer(
        f"✅ Товар успешно добавлен!\n\n"
        f"📦 ID: {product_id}\n"
        f"📝 Название: {data['product_name']}\n"
        f"💰 Цена: {data['product_price']}₽\n"
        f"📂 Категория: {data['product_category']}",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin_edit_products")
async def admin_edit_products(callback: CallbackQuery, state: FSMContext):
    """Просмотр всех товаров для редактирования"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    products = await get_all_products()
    if not products:
        await callback.message.edit_text(
            "📦 В базе данных нет товаров.",
            reply_markup=get_admin_panel_keyboard()
        )
        return
    
    await state.set_state(AdminStates.admin_menu)
    await callback.message.edit_text(
        "📦 Список всех товаров:\n\n"
        "Выберите товар для редактирования:",
        reply_markup=get_admin_products_keyboard(products)
    )


@router.callback_query(F.data.startswith("admin_edit_product:"))
async def admin_edit_product(callback: CallbackQuery, state: FSMContext):
    """Редактирование конкретного товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return
    
    await state.update_data(editing_product_id=product_id)
    await state.set_state(AdminStates.admin_menu)
    
    status = "✅ Активен" if product["is_active"] else "❌ Неактивен"
    await callback.message.edit_text(
        f"📦 Товар #{product['id']}\n\n"
        f"📝 Название: {product['name']}\n"
        f"📄 Описание: {product['description']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📂 Категория: {product['category']}\n"
        f"📎 Файл: {'Есть' if product['file_path'] else 'Нет'}\n"
        f"🔗 Ссылка: {product['download_link'] or 'Нет'}\n"
        f"📊 Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_edit_name:"))
async def admin_edit_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(editing_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_name)
    await callback.message.edit_text(
        "✏️ Введите новое название товара:"
    )


@router.message(AdminStates.waiting_edit_product_name)
async def admin_edit_name(message: Message, state: FSMContext):
    """Получение нового названия"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    product_name = message.text.strip()
    if len(product_name) < 2:
        await message.answer("❌ Название должно быть не короче 2 символов. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data["editing_product_id"]
    
    if not db.connection:
        await db.connect()
    
    await db.connection.execute(
        "UPDATE products SET name = ? WHERE id = ?",
        (product_name, product_id)
    )
    await db.connection.commit()
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    product = await get_product_by_id(product_id)
    await message.answer(
        f"✅ Название товара обновлено!\n\n"
        f"📦 Товар #{product['id']}\n"
        f"📝 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📂 Категория: {product['category']}",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_edit_description:"))
async def admin_edit_description_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(editing_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_description)
    await callback.message.edit_text(
        "✏️ Введите новое описание товара:"
    )


@router.message(AdminStates.waiting_edit_product_description)
async def admin_edit_description(message: Message, state: FSMContext):
    """Получение нового описания"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    product_description = message.text.strip()
    if len(product_description) < 5:
        await message.answer("❌ Описание должно быть не короче 5 символов. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data["editing_product_id"]
    
    if not db.connection:
        await db.connect()
    
    await db.connection.execute(
        "UPDATE products SET description = ? WHERE id = ?",
        (product_description, product_id)
    )
    await db.connection.commit()
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    product = await get_product_by_id(product_id)
    await message.answer(
        f"✅ Описание товара обновлено!\n\n"
        f"📦 Товар #{product['id']}\n"
        f"📝 Название: {product['name']}\n"
        f"📄 Описание: {product['description']}\n"
        f"💰 Цена: {product['price']}₽",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_edit_price:"))
async def admin_edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(editing_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_price)
    await callback.message.edit_text(
        "✏️ Введите новую цену товара (в рублях):"
    )


@router.message(AdminStates.waiting_edit_product_price)
async def admin_edit_price(message: Message, state: FSMContext):
    """Получение новой цены"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число). Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data["editing_product_id"]
    
    if not db.connection:
        await db.connect()
    
    await db.connection.execute(
        "UPDATE products SET price = ? WHERE id = ?",
        (price, product_id)
    )
    await db.connection.commit()
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    product = await get_product_by_id(product_id)
    await message.answer(
        f"✅ Цена товара обновлена!\n\n"
        f"📦 Товар #{product['id']}\n"
        f"📝 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📂 Категория: {product['category']}",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_edit_category:"))
async def admin_edit_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(editing_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_category)
    await callback.message.edit_text(
        "✏️ Введите новую категорию товара:"
    )


@router.message(AdminStates.waiting_edit_product_category)
async def admin_edit_category(message: Message, state: FSMContext):
    """Получение новой категории"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    category = message.text.strip()
    if len(category) < 2:
        await message.answer("❌ Категория должна быть не короче 2 символов. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data["editing_product_id"]
    
    if not db.connection:
        await db.connect()
    
    await db.connection.execute(
        "UPDATE products SET category = ? WHERE id = ?",
        (category, product_id)
    )
    await db.connection.commit()
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    product = await get_product_by_id(product_id)
    await message.answer(
        f"✅ Категория товара обновлена!\n\n"
        f"📦 Товар #{product['id']}\n"
        f"📝 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📂 Категория: {product['category']}",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_edit_file:"))
async def admin_edit_file_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования файла"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(editing_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_file)
    await callback.message.edit_text(
        "✏️ Отправьте новый файл товара (или введите ссылку на скачивание):"
    )


@router.message(AdminStates.waiting_edit_product_file)
async def admin_edit_file(message: Message, state: FSMContext):
    """Получение нового файла"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    data = await state.get_data()
    product_id = data["editing_product_id"]
    
    file_path = None
    download_link = None
    
    if message.document:
        file_info = message.document
        file_path = f"files/products/{file_info.file_unique_id}_{file_info.file_name}"
        
        import os
        os.makedirs("files/products", exist_ok=True)
        
        destination = file_path
        await message.bot.download(file_info, destination)
        
        download_link = None
        await message.answer("✅ Файл получен и сохранен.")
    elif message.text:
        download_link = message.text.strip()
        if not download_link.startswith(("http://", "https://")):
            await message.answer("❌ Ссылка должна начинаться с http:// или https://. Попробуйте еще раз:")
            return
        await message.answer("✅ Ссылка получена.")
    else:
        await message.answer("❌ Отправьте файл или введите ссылку на скачивание:")
        return
    
    if not db.connection:
        await db.connect()
    
    await db.connection.execute(
        "UPDATE products SET file_path = ?, download_link = ? WHERE id = ?",
        (file_path, download_link, product_id)
    )
    await db.connection.commit()
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    product = await get_product_by_id(product_id)
    await message.answer(
        f"✅ Файл товара обновлен!\n\n"
        f"📦 Товар #{product['id']}\n"
        f"📝 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📎 Файл: {'Есть' if product['file_path'] else 'Нет'}\n"
        f"🔗 Ссылка: {product['download_link'] or 'Нет'}",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_edit_link:"))
async def admin_edit_link_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования ссылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(editing_product_id=product_id)
    await state.set_state(AdminStates.waiting_edit_product_link)
    await callback.message.edit_text(
        "✏️ Введите новую ссылку на скачивание товара:"
    )


@router.message(AdminStates.waiting_edit_product_link)
async def admin_edit_link(message: Message, state: FSMContext):
    """Получение новой ссылки"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    download_link = message.text.strip()
    if not download_link.startswith(("http://", "https://")):
        await message.answer("❌ Ссылка должна начинаться с http:// или https://. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    product_id = data["editing_product_id"]
    
    if not db.connection:
        await db.connect()
    
    await db.connection.execute(
        "UPDATE products SET download_link = ? WHERE id = ?",
        (download_link, product_id)
    )
    await db.connection.commit()
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    product = await get_product_by_id(product_id)
    await message.answer(
        f"✅ Ссылка товара обновлена!\n\n"
        f"📦 Товар #{product['id']}\n"
        f"📝 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"🔗 Ссылка: {product['download_link']}",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_toggle_product:"))
async def admin_toggle_product(callback: CallbackQuery, state: FSMContext):
    """Активация/деактивация товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return
    
    new_status = 0 if product["is_active"] else 1
    
    if not db.connection:
        await db.connect()
    
    await db.connection.execute(
        "UPDATE products SET is_active = ? WHERE id = ?",
        (new_status, product_id)
    )
    await db.connection.commit()
    
    product = await get_product_by_id(product_id)
    status = "✅ Активен" if product["is_active"] else "❌ Неактивен"
    
    await callback.message.edit_text(
        f"📦 Товар #{product['id']}\n\n"
        f"📝 Название: {product['name']}\n"
        f"📄 Описание: {product['description']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📂 Категория: {product['category']}\n"
        f"📎 Файл: {'Есть' if product['file_path'] else 'Нет'}\n"
        f"🔗 Ссылка: {product['download_link'] or 'Нет'}\n"
        f"📊 Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_delete_product:"))
async def admin_delete_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return
    
    await state.update_data(deleting_product_id=product_id)
    await state.set_state(AdminStates.waiting_delete_confirm)
    
    await callback.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить товар?\n\n"
        f"📦 Товар #{product['id']}\n"
        f"📝 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=get_admin_confirm_keyboard(product_id)
    )


@router.callback_query(F.data.startswith("admin_confirm_delete:"))
async def admin_confirm_delete(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    if not db.connection:
        await db.connect()
    
    # Удаляем товар из корзин пользователей
    await db.connection.execute(
        "DELETE FROM cart WHERE product_id = ?",
        (product_id,)
    )
    
    # Удаляем товар
    await db.connection.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )
    await db.connection.commit()
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    await callback.message.edit_text(
        f"✅ Товар #{product_id} успешно удален!",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data.startswith("admin_cancel_delete:"))
async def admin_cancel_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    
    status = "✅ Активен" if product["is_active"] else "❌ Неактивен"
    await callback.message.edit_text(
        f"📦 Товар #{product['id']}\n\n"
        f"📝 Название: {product['name']}\n"
        f"📄 Описание: {product['description']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📂 Категория: {product['category']}\n"
        f"📎 Файл: {'Есть' if product['file_path'] else 'Нет'}\n"
        f"🔗 Ссылка: {product['download_link'] or 'Нет'}\n"
        f"📊 Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_product_actions_keyboard(product_id)
    )


@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery, state: FSMContext):
    """Просмотр категорий"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    categories = await get_all_categories()
    if not categories:
        await callback.message.edit_text(
            "📂 В базе данных нет категорий.",
            reply_markup=get_admin_panel_keyboard()
        )
        return
    
    await state.set_state(AdminStates.admin_menu)
    await callback.message.edit_text(
        "📂 Список всех категорий:\n\n" +
        "\n".join([f"• {cat}" for cat in categories]),
        reply_markup=get_admin_categories_keyboard(categories)
    )


@router.callback_query(F.data == "admin_back_to_panel")
async def admin_back_to_panel(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    await state.clear()
    await state.set_state(AdminStates.admin_menu)
    await callback.message.edit_text(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, state: FSMContext):
    """Просмотр статистики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа к админ-панели.", show_alert=True)
        return
    
    if not db.connection:
        await db.connect()
    
    # Получаем статистику
    cursor = await db.connection.execute("SELECT COUNT(*) FROM users")
    users_count = (await cursor.fetchone())[0]
    
    cursor = await db.connection.execute("SELECT COUNT(*) FROM products")
    products_count = (await cursor.fetchone())[0]
    
    cursor = await db.connection.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
    active_products = (await cursor.fetchone())[0]
    
    cursor = await db.connection.execute("SELECT COUNT(*) FROM orders")
    orders_count = (await cursor.fetchone())[0]
    
    cursor = await db.connection.execute("SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status
