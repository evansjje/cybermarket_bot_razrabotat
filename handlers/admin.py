# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_stats, get_all_products
from keyboards import admin_menu_kb, main_menu_kb
from config import settings

router = Router()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message) -> None:
    """Открыть админ-панель"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "⚡ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message) -> None:
    """Показать статистику бота"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    stats = await get_stats()
    
    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📦 Товаров: <b>{stats['products']}</b>\n"
        f"📁 Категорий: <b>{stats['categories']}</b>\n"
        f"🛒 Заказов: <b>{stats['orders']}</b>\n"
    )
    
    await message.answer(text, reply_markup=admin_menu_kb())


@router.message(F.text == '📦 Список товаров')
async def show_products_list(message: Message) -> None:
    """Показать список всех товаров"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    products = await get_all_products()
    
    if not products:
        await message.answer(
            "📦 Список товаров пуст.\n\n"
            "Добавьте товары через ➕ Добавить товар",
            reply_markup=admin_menu_kb()
        )
        return
    
    lines = []
    for product in products:
        product_id, category_id, name, description, price = product
        lines.append(
            f"🆔 <b>{product_id}</b> | {name}\n"
            f"   💰 {price:.2f} ₽ | Категория: {category_id}"
        )
    
    text = "📦 <b>Все товары:</b>\n\n" + "\n\n".join(lines)
    
    await message.answer(text, reply_markup=admin_menu_kb())


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message) -> None:
    """Вернуться в главное меню"""
    user_id = message.from_user.id
    await message.answer(
        "Вы вернулись в главное меню:",
        reply_markup=main_menu_kb(user_id)
    )
