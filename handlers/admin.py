import logging
from typing import List, Dict, Any, Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from config import Settings
from database import Database
from keyboards import (
    get_admin_menu,
    get_admin_products_menu,
    get_admin_product_edit_menu,
    get_admin_categories_menu,
    get_admin_confirm_menu,
    get_main_menu
)

logger = logging.getLogger(__name__)
settings = Settings()

router = Router()
db = Database(settings.DB_PATH)


class AdminStates(StatesGroup):
    """Состояния для админ-панели."""
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_category = State()
    waiting_product_file_id = State()
    waiting_product_media = State()
    waiting_edit_product_name = State()
    waiting_edit_product_description = State()
    waiting_edit_product_price = State()
    waiting_edit_product_category = State()
    waiting_edit_product_file_id = State()
    waiting_edit_product_media = State()
    waiting_delete_product_confirm = State()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Открывает админ-панель."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🛠 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )


@router.message(F.text == "🛠 Админ-панель")
async def admin_panel_message(message: Message):
    """Открывает админ-панель через кнопку."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🛠 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    """Возврат в админ-меню."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🛠 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начинает добавление товара."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await state.clear()
    await state.set_state(AdminStates.waiting_product_name)
    await callback.message.edit_text(
        "➕ Добавление нового товара\n\n"
        "Введите название товара:"
    )


@router.message(AdminStates.waiting_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    """Получает название товара."""
    product_name = message.text.strip()
    if not product_name:
        await message.answer("❌ Название не может быть пустым. Введите название:")
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer("📝 Введите описание товара:")


@router.message(AdminStates.waiting_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    """Получает описание товара."""
    description = message.text.strip()
    if not description:
        await message.answer("❌ Описание не может быть пустым. Введите описание:")
        return
    
    await state.update_data(product_description=description)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer("💰 Введите цену товара (в рублях):")


@router.message(AdminStates.waiting_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получает цену товара."""
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    await state.update_data(product_price=price)
    
    categories = await db.get_categories()
    if not categories:
        categories = settings.DEFAULT_CATEGORIES
    
    await state.set_state(AdminStates.waiting_product_category)
    await message.answer(
        "📁 Выберите категорию товара:",
        reply_markup=get_admin_categories_menu(categories)
    )


@router.callback_query(AdminStates.waiting_product_category, F.data.startswith("admin_cat:"))
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    """Получает категорию товара."""
    category = callback.data.split(":", 1)[1]
    await state.update_data(product_category=category)
    await state.set_state(AdminStates.waiting_product_file_id)
    await callback.message.edit_text(
        "📎 Отправьте файл товара (или ссылку на файл):"
    )


@router.message(AdminStates.waiting_product_file_id)
async def admin_add_product_file(message: Message, state: FSMContext):
    """Получает файл товара."""
    file_id = None
    file_link = None
    
    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.startswith("http"):
        file_link = message.text.strip()
    else:
        await message.answer("❌ Отправьте файл или ссылку на файл:")
        return
    
    await state.update_data(
        product_file_id=file_id,
        product_file_link=file_link
    )
    await state.set_state(AdminStates.waiting_product_media)
    await message.answer(
        "🖼 Отправьте медиафайл для товара (фото, видео) или нажмите 'Пропустить':\n\n"
        "Или отправьте /skip для пропуска"
    )


@router.message(AdminStates.waiting_product_media, F.text == "/skip")
async def admin_add_product_media_skip(message: Message, state: FSMContext):
    """Пропускает загрузку медиа."""
    data = await state.get_data()
    
    try:
        product_id = await db.add_product(
            name=data["product_name"],
            description=data["product_description"],
            price=data["product_price"],
            category=data["product_category"],
            file_id=data.get("product_file_id"),
            file_link=data.get("product_file_link"),
            media_id=None
        )
        
        await state.clear()
        await message.answer(
            f"✅ Товар успешно добавлен!\n\n"
            f"ID: {product_id}\n"
            f"Название: {data['product_name']}\n"
            f"Цена: {data['product_price']} {settings.CURRENCY}\n"
            f"Категория: {data['product_category']}",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        await message.answer("❌ Ошибка при добавлении товара. Попробуйте позже.")
        await state.clear()


@router.message(AdminStates.waiting_product_media)
async def admin_add_product_media(message: Message, state: FSMContext):
    """Получает медиафайл товара."""
    media_id = None
    
    if message.photo:
        media_id = message.photo[-1].file_id
    elif message.video:
        media_id = message.video.file_id
    elif message.animation:
        media_id = message.animation.file_id
    else:
        await message.answer("❌ Отправьте фото, видео или GIF, или /skip для пропуска:")
        return
    
    data = await state.get_data()
    
    try:
        product_id = await db.add_product(
            name=data["product_name"],
            description=data["product_description"],
            price=data["product_price"],
            category=data["product_category"],
            file_id=data.get("product_file_id"),
            file_link=data.get("product_file_link"),
            media_id=media_id
        )
        
        await state.clear()
        await message.answer(
            f"✅ Товар успешно добавлен!\n\n"
            f"ID: {product_id}\n"
            f"Название: {data['product_name']}\n"
            f"Цена: {data['product_price']} {settings.CURRENCY}\n"
            f"Категория: {data['product_category']}",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        await message.answer("❌ Ошибка при добавлении товара. Попробуйте позже.")
        await state.clear()


@router.callback_query(F.data == "admin_edit_product")
async def admin_edit_product_list(callback: CallbackQuery):
    """Показывает список товаров для редактирования."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    try:
        products = await db.get_all_products()
        if not products:
            await callback.message.edit_text(
                "📦 Товары не найдены.",
                reply_markup=get_admin_menu()
            )
            return
        
        await callback.message.edit_text(
            "📦 Выберите товар для редактирования:",
            reply_markup=get_admin_products_menu(products)
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка товаров: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении списка товаров.",
            reply_markup=get_admin_menu()
        )


@router.callback_query(F.data.startswith("admin_edit_product:"))
async def admin_edit_product_detail(callback: CallbackQuery, state: FSMContext):
    """Показывает детали товара для редактирования."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    product_id = int(callback.data.split(":", 1)[1])
    
    try:
        product = await db.get_product(product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return
        
        await state.update_data(edit_product_id=product_id)
        
        product_info = (
            f"📦 Товар #{product['id']}\n\n"
            f"📝 Название: {product['name']}\n"
            f"📄 Описание: {product['description']}\n"
            f"💰 Цена: {product['price']} {settings.CURRENCY}\n"
            f"📁 Категория: {product['category']}\n"
            f"📎 Файл: {'Да' if product.get('file_id') or product.get('file_link') else 'Нет'}\n"
            f"🖼 Медиа: {'Да' if product.get('media_id') else 'Нет'}"
        )
        
        await callback.message.edit_text(
            product_info,
            reply_markup=get_admin_product_edit_menu(product_id)
        )
    except Exception as e:
        logger.error(f"Ошибка при получении товара: {e}")
        await callback.answer("❌ Ошибка при получении товара", show_alert=True)


@router.callback_query(F.data.startswith("admin_edit_name:"))
async def admin_edit_product_name_start(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование названия."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_edit_product_name)
    await callback.message.edit_text(
        "📝 Введите новое название товара:"
    )


@router.message(AdminStates.waiting_edit_product_name)
async def admin_edit_product_name(message: Message, state: FSMContext):
    """Получает новое название товара."""
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название не может быть пустым. Введите название:")
        return
    
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    try:
        await db.update_product(product_id, name=name)
        await state.clear()
        await message.answer(
            "✅ Название товара обновлено!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении названия: {e}")
        await message.answer("❌ Ошибка при обновлении названия.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_edit_description:"))
async def admin_edit_product_description_start(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование описания."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_edit_product_description)
    await callback.message.edit_text(
        "📝 Введите новое описание товара:"
    )


@router.message(AdminStates.waiting_edit_product_description)
async def admin_edit_product_description(message: Message, state: FSMContext):
    """Получает новое описание товара."""
    description = message.text.strip()
    if not description:
        await message.answer("❌ Описание не может быть пустым. Введите описание:")
        return
    
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    try:
        await db.update_product(product_id, description=description)
        await state.clear()
        await message.answer(
            "✅ Описание товара обновлено!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении описания: {e}")
        await message.answer("❌ Ошибка при обновлении описания.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_edit_price:"))
async def admin_edit_product_price_start(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование цены."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_edit_product_price)
    await callback.message.edit_text(
        "💰 Введите новую цену товара (в рублях):"
    )


@router.message(AdminStates.waiting_edit_product_price)
async def admin_edit_product_price(message: Message, state: FSMContext):
    """Получает новую цену товара."""
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число):")
        return
    
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    try:
        await db.update_product(product_id, price=price)
        await state.clear()
        await message.answer(
            "✅ Цена товара обновлена!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении цены: {e}")
        await message.answer("❌ Ошибка при обновлении цены.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_edit_category:"))
async def admin_edit_product_category_start(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование категории."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    categories = await db.get_categories()
    if not categories:
        categories = settings.DEFAULT_CATEGORIES
    
    await state.set_state(AdminStates.waiting_edit_product_category)
    await callback.message.edit_text(
        "📁 Выберите новую категорию:",
        reply_markup=get_admin_categories_menu(categories)
    )


@router.callback_query(AdminStates.waiting_edit_product_category, F.data.startswith("admin_cat:"))
async def admin_edit_product_category(callback: CallbackQuery, state: FSMContext):
    """Получает новую категорию товара."""
    category = callback.data.split(":", 1)[1]
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    try:
        await db.update_product(product_id, category=category)
        await state.clear()
        await callback.message.edit_text(
            "✅ Категория товара обновлена!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении категории: {e}")
        await callback.message.edit_text("❌ Ошибка при обновлении категории.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_edit_file:"))
async def admin_edit_product_file_start(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование файла."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_edit_product_file_id)
    await callback.message.edit_text(
        "📎 Отправьте новый файл товара (или ссылку на файл):"
    )


@router.message(AdminStates.waiting_edit_product_file_id)
async def admin_edit_product_file(message: Message, state: FSMContext):
    """Получает новый файл товара."""
    file_id = None
    file_link = None
    
    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.startswith("http"):
        file_link = message.text.strip()
    else:
        await message.answer("❌ Отправьте файл или ссылку на файл:")
        return
    
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    try:
        await db.update_product(
            product_id,
            file_id=file_id,
            file_link=file_link
        )
        await state.clear()
        await message.answer(
            "✅ Файл товара обновлен!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении файла: {e}")
        await message.answer("❌ Ошибка при обновлении файла.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_edit_media:"))
async def admin_edit_product_media_start(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование медиа."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_edit_product_media)
    await callback.message.edit_text(
        "🖼 Отправьте новый медиафайл (фото, видео, GIF) или /skip для удаления:"
    )


@router.message(AdminStates.waiting_edit_product_media, F.text == "/skip")
async def admin_edit_product_media_skip(message: Message, state: FSMContext):
    """Удаляет медиа товара."""
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    try:
        await db.update_product(product_id, media_id=None)
        await state.clear()
        await message.answer(
            "✅ Медиа товара удалено!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении медиа: {e}")
        await message.answer("❌ Ошибка при удалении медиа.")
        await state.clear()


@router.message(AdminStates.waiting_edit_product_media)
async def admin_edit_product_media(message: Message, state: FSMContext):
    """Получает новый медиафайл товара."""
    media_id = None
    
    if message.photo:
        media_id = message.photo[-1].file_id
    elif message.video:
        media_id = message.video.file_id
    elif message.animation:
        media_id = message.animation.file_id
    else:
        await message.answer("❌ Отправьте фото, видео или GIF, или /skip для удаления:")
        return
    
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    try:
        await db.update_product(product_id, media_id=media_id)
        await state.clear()
        await message.answer(
            "✅ Медиа товара обновлено!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении медиа: {e}")
        await message.answer("❌ Ошибка при обновлении медиа.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_delete_product:"))
async def admin_delete_product_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    product_id = int(callback.data.split(":", 1)[1])
    await state.update_data(delete_product_id=product_id)
    await state.set_state(AdminStates.waiting_delete_product_confirm)
    
    await callback.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить товар #{product_id}?\n\n"
        f"Это действие нельзя отменить.",
        reply_markup=get_admin_confirm_menu()
    )


@router.callback_query(AdminStates.waiting_delete_product_confirm, F.data == "admin_confirm_yes")
async def admin_delete_product_yes(callback: CallbackQuery, state: FSMContext):
    """Удаляет товар."""
    data = await state.get_data()
    product_id = data.get("delete_product_id")
    
    try:
        await db.delete_product(product_id)
        await state.clear()
        await callback.message.edit_text(
            f"✅ Товар #{product_id} удален!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при удалении товара.",
            reply_markup=get_admin_menu()
        )
        await state.clear()


@router.callback_query(AdminStates.waiting_delete_product_confirm, F.data == "admin_confirm_no")
async def admin_delete_product_no(callback: CallbackQuery, state: FSMContext):
    """Отменяет удаление товара."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Удаление отменено.",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_products_list")
async def admin_products_list(callback: CallbackQuery):
    """Показывает список всех товаров."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    try:
        products = await db.get_all_products()
        if not products:
            await callback.message.edit_text(
                "📦 Товары не найдены.",
                reply_markup=get_admin_menu()
            )
            return
        
        text = "📦 Все товары:\n\n"
        for product in products:
            text += (
                f"#{product['id']} | {product['name']}\n"
                f"💰 {product['price']} {settings.CURRENCY} | 📁 {product['category']}\n\n"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка товаров: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении списка товаров.",
            reply_markup=get_admin_menu()
        )


@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    """Показывает статистику заказов."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    try:
        stats = await db.get_order_stats()
        await callback.message.edit_text(
            f"📊 Статистика заказов:\n\n"
            f"Всего заказов: {stats.get('total_orders', 0)}\n"
            f"Успешных: {stats.get('successful_orders', 0)}\n"
            f"Общая выручка: {stats.get('total_revenue', 0)} {settings.CURRENCY}",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики.",
            reply_markup=get_admin_menu()
        )


@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Показывает статистику пользователей."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    try:
        users_count = await db.get_users_count()
        await callback.message.edit_text(
            f"👥 Пользователи:\n\n"
            f"Всего пользователей: {users_count}",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователей: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики.",
            reply_markup=get_admin_menu()
        )
