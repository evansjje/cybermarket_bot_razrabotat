# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_categories, get_products_by_category, get_product, add_to_cart
from keyboards import main_menu_kb, product_card_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.message(F.text == '🛍 Каталог')
async def show_categories(message: Message) -> None:
    """Показ списка категорий"""
    categories = await get_categories()
    
    if not categories:
        await message.answer("📭 Каталог пуст. Товары появятся позже.")
        return
    
    builder = InlineKeyboardBuilder()
    for cat_id, cat_name in categories:
        builder.row(InlineKeyboardButton(
            text=cat_name,
            callback_data=f'category:{cat_id}'
        ))
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='back_to_main'
    ))
    
    await message.answer(
        "🛍 Выберите категорию:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith('category:'))
async def show_products(callback: CallbackQuery) -> None:
    """Показ товаров выбранной категории"""
    await callback.answer()
    
    category_id = int(callback.data.split(':')[1])
    products = await get_products_by_category(category_id)
    
    if not products:
        await callback.message.edit_text(
            "📭 В этой категории пока нет товаров.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_catalog')
            ]])
        )
        return
    
    # Показываем первый товар категории
    product = products[0]
    await show_product_card(callback.message, product)


async def show_product_card(message, product) -> None:
    """Отображение карточки товара"""
    product_id, name, description, price = product
    
    text = (
        f"📦 <b>{name}</b>\n\n"
        f"{description}\n\n"
        f"💰 Цена: <b>{price:.2f} ₽</b>"
    )
    
    await message.edit_text(
        text,
        reply_markup=product_card_kb(product_id),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'back_to_catalog')
async def back_to_catalog(callback: CallbackQuery) -> None:
    """Возврат к списку категорий"""
    await callback.answer()
    
    categories = await get_categories()
    
    builder = InlineKeyboardBuilder()
    for cat_id, cat_name in categories:
        builder.row(InlineKeyboardButton(
            text=cat_name,
            callback_data=f'category:{cat_id}'
        ))
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='back_to_main'
    ))
    
    await callback.message.edit_text(
        "🛍 Выберите категорию:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery) -> None:
    """Возврат в главное меню"""
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_kb(callback.from_user.id)
    )


@router.callback_query(F.data.startswith('add_to_cart:'))
async def add_to_cart_handler(callback: CallbackQuery) -> None:
    """Добавление товара в корзину"""
    await callback.answer("Товар добавлен!")
    
    product_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    await add_to_cart(user_id, product_id)
    
    # Показываем уведомление
    product = await get_product(product_id)
    if product:
        await callback.message.answer(
            f"✅ <b>{product[1]}</b> добавлен в корзину!\n\n"
            "Продолжайте покупки или перейдите в корзину.",
            parse_mode='HTML'
        )
