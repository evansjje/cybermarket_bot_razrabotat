from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import get_stats, get_all_products, delete_product, get_categories
from keyboards import admin_menu_kb, main_menu_kb, admin_products_kb

router = Router()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message):
    user_id = message.from_user.id
    if user_id not in [admin_id for admin_id in __import__('config').settings.ADMIN_IDS]:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "⚡ Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message):
    user_id = message.from_user.id
    if user_id not in [admin_id for admin_id in __import__('config').settings.ADMIN_IDS]:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    stats = await get_stats()
    
    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📦 Товаров: <b>{stats['products']}</b>\n"
        f"🛒 Заказов: <b>{stats['orders']}</b>\n"
        f"💰 Выручка: <b>{stats['revenue']}₽</b>"
    )
    
    await message.answer(text, reply_markup=admin_menu_kb())


@router.message(F.text == '📦 Список товаров')
async def show_products(message: Message):
    user_id = message.from_user.id
    if user_id not in [admin_id for admin_id in __import__('config').settings.ADMIN_IDS]:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    products = await get_all_products()
    
    if not products:
        await message.answer(
            "📦 Список товаров пуст.\n\n"
            "Добавьте товары через кнопку ➕ Добавить товар",
            reply_markup=admin_menu_kb()
        )
        return
    
    await message.answer(
        "📦 <b>Список товаров:</b>\n\n"
        "Нажмите на товар, чтобы удалить его.",
        reply_markup=admin_products_kb(products)
    )


@router.callback_query(F.data.startswith('del_prod_'))
async def delete_product_handler(callback: CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    if user_id not in [admin_id for admin_id in __import__('config').settings.ADMIN_IDS]:
        await callback.message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    product_id = int(callback.data.split('_')[2])
    await delete_product(product_id)
    
    products = await get_all_products()
    
    if products:
        await callback.message.edit_text(
            "✅ Товар удален!\n\n"
            "📦 <b>Список товаров:</b>\n\n"
            "Нажмите на товар, чтобы удалить его.",
            reply_markup=admin_products_kb(products)
        )
    else:
        await callback.message.edit_text(
            "✅ Товар удален!\n\n"
            "📦 Список товаров пуст.\n\n"
            "Добавьте товары через кнопку ➕ Добавить товар"
        )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message):
    user_id = message.from_user.id
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_kb(user_id)
    )
