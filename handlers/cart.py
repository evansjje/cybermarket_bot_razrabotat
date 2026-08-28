from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_cart, clear_cart, get_user_cart_total
from keyboards import main_menu_kb, cart_kb

router = Router()


@router.message(F.text == '🛒 Корзина')
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста\n\n"
            "Загляните в каталог и выберите товары!",
            reply_markup=main_menu_kb(user_id)
        )
        return
    
    total = await get_user_cart_total(user_id)
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        cart_text += (
            f"📦 <b>{item['title']}</b>\n"
            f"💰 Цена: {item['price']}₽\n"
            f"📊 Количество: {item['count']}\n"
            f"─────────────\n"
        )
    
    cart_text += f"\n💎 <b>Итого: {total}₽</b>"
    
    await message.answer(
        cart_text,
        reply_markup=cart_kb()
    )


@router.callback_query(F.data == 'clear_cart')
async def clear_cart_handler(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await clear_cart(user_id)
    
    await callback.message.edit_text(
        "🗑 Корзина очищена!\n\n"
        "Загляните в каталог и выберите товары!",
        reply_markup=main_menu_kb(user_id)
    )


@router.callback_query(F.data == 'checkout')
async def checkout_handler(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста!\n\n"
            "Добавьте товары из каталога.",
            reply_markup=main_menu_kb(user_id)
        )
        return
    
    total = await get_user_cart_total(user_id)
    
    # Заглушка создания счета
    await callback.message.edit_text(
        f"💳 <b>Оплата заказа</b>\n\n"
        f"Сумма к оплате: <b>{total}₽</b>\n\n"
        f"🔗 Ссылка для оплаты будет отправлена после подтверждения.\n\n"
        f"⏳ Ожидайте подтверждение оплаты...",
        reply_markup=main_menu_kb(user_id)
    )
