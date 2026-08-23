import logging
from typing import Optional, Dict, Any, List

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from config import Settings
from database import Database
from keyboards import (
    get_payment_methods_menu,
    get_payment_success_menu,
    get_main_menu,
    get_product_detail_menu
)

logger = logging.getLogger(__name__)
settings = Settings()

router = Router()
db = Database(settings.DB_PATH)


class PaymentStates(StatesGroup):
    """Состояния для процесса оплаты."""
    choosing_payment_method = State()
    processing_payment = State()


@router.callback_query(F.data.startswith("checkout:"))
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс оформления заказа."""
    try:
        user_id = callback.from_user.id
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            await callback.answer("🛒 Ваша корзина пуста!", show_alert=True)
            return
        
        total_price = sum(item["price"] * item["quantity"] for item in cart_items)
        
        await state.update_data(
            cart_items=cart_items,
            total_price=total_price
        )
        
        await callback.message.edit_text(
            f"💰 Оформление заказа\n\n"
            f"Сумма к оплате: {total_price} {settings.CURRENCY}\n\n"
            f"Выберите способ оплаты:",
            reply_markup=get_payment_methods_menu()
        )
        await state.set_state(PaymentStates.choosing_payment_method)
        
    except Exception as e:
        logger.error(f"Ошибка при оформлении заказа: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "payment:telegram")
async def pay_with_telegram(callback: CallbackQuery, state: FSMContext):
    """Оплата через Telegram Payments."""
    try:
        if not settings.TELEGRAM_PAYMENT_TOKEN:
            await callback.answer("❌ Telegram Payments не настроен. Используйте YooKassa.", show_alert=True)
            return
        
        data = await state.get_data()
        total_price = data.get("total_price", 0)
        cart_items = data.get("cart_items", [])
        
        # Создаем описание заказа
        items_description = "\n".join(
            f"• {item['name']} x{item['quantity']}" for item in cart_items
        )
        
        prices = [
            LabeledPrice(
                label=f"{item['name']} x{item['quantity']}",
                amount=int(item["price"] * item["quantity"] * 100)  # В копейках
            )
            for item in cart_items
        ]
        
        await callback.message.answer_invoice(
            title="Покупка в CyberMarket",
            description=items_description,
            payload=f"order_{callback.from_user.id}_{int(__import__('time').time())}",
            provider_token=settings.TELEGRAM_PAYMENT_TOKEN,
            currency=settings.CURRENCY,
            prices=prices,
            start_parameter="cybermarket_payment"
        )
        
        await state.set_state(PaymentStates.processing_payment)
        
    except Exception as e:
        logger.error(f"Ошибка при оплате через Telegram: {e}")
        await callback.answer("❌ Ошибка при создании платежа.", show_alert=True)


@router.callback_query(F.data == "payment:yookassa")
async def pay_with_yookassa(callback: CallbackQuery, state: FSMContext):
    """Оплата через YooKassa."""
    try:
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            await callback.answer("❌ YooKassa не настроен. Используйте Telegram Payments.", show_alert=True)
            return
        
        data = await state.get_data()
        total_price = data.get("total_price", 0)
        cart_items = data.get("cart_items", [])
        
        # Здесь должна быть интеграция с YooKassa API
        # Для примера используем Telegram Payments как fallback
        if settings.TELEGRAM_PAYMENT_TOKEN:
            await pay_with_telegram(callback, state)
        else:
            await callback.answer("❌ Нет доступных способов оплаты.", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка при оплате через YooKassa: {e}")
        await callback.answer("❌ Ошибка при создании платежа.", show_alert=True)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Обработчик предварительной проверки платежа."""
    try:
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        logger.error(f"Ошибка в pre_checkout: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Ошибка при проверке платежа")


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, state: FSMContext):
    """Обработчик успешного платежа."""
    try:
        user_id = message.from_user.id
        payment_info = message.successful_payment
        
        # Получаем данные заказа
        data = await state.get_data()
        cart_items = data.get("cart_items", [])
        total_price = data.get("total_price", 0)
        
        # Создаем заказ в базе данных
        order_id = await db.create_order(
            user_id=user_id,
            items=cart_items,
            total_price=total_price,
            payment_method="telegram_payments",
            payment_id=payment_info.provider_payment_charge_id
        )
        
        # Очищаем корзину
        await db.clear_cart(user_id)
        
        # Начисляем реферальные бонусы
        await db.process_referral_bonus(user_id, total_price)
        
        # Получаем ссылки на товары
        product_links = []
        for item in cart_items:
            product = await db.get_product(item["product_id"])
            if product:
                if product.get("file_path"):
                    product_links.append(f"📦 {product['name']}: {product['file_path']}")
                elif product.get("download_link"):
                    product_links.append(f"📦 {product['name']}: {product['download_link']}")
                else:
                    product_links.append(f"📦 {product['name']}: файл будет отправлен администратором")
        
        # Отправляем сообщение об успешной оплате
        success_message = (
            f"✅ Оплата прошла успешно!\n\n"
            f"💰 Сумма: {total_price} {settings.CURRENCY}\n"
            f"📋 Номер заказа: #{order_id}\n\n"
            f"📦 Ваши товары:\n"
            f"{chr(10).join(product_links)}\n\n"
            f"Спасибо за покупку! 🎉"
        )
        
        await message.answer(
            success_message,
            reply_markup=get_payment_success_menu()
        )
        
        # Уведомляем администратора
        for admin_id in settings.ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🛒 Новая покупка!\n\n"
                    f"👤 Пользователь: @{message.from_user.username or message.from_user.id}\n"
                    f"💰 Сумма: {total_price} {settings.CURRENCY}\n"
                    f"📋 Заказ: #{order_id}"
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить админа {admin_id}: {e}")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа: {e}")
        await message.answer("❌ Произошла ошибка при обработке платежа. Обратитесь в поддержку.")


@router.callback_query(F.data == "payment:cancel")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отмена оплаты."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Оплата отменена.\n"
        "Вы можете продолжить покупки в каталоге.",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "payment:retry")
async def retry_payment(callback: CallbackQuery, state: FSMContext):
    """Повторная попытка оплаты."""
    data = await state.get_data()
    if not data:
        await callback.answer("❌ Сессия оплаты истекла. Попробуйте снова.", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"💰 Сумма к оплате: {data.get('total_price', 0)} {settings.CURRENCY}\n\n"
        f"Выберите способ оплаты:",
        reply_markup=get_payment_methods_menu()
    )


@router.message(Command("buy"))
async def cmd_buy(message: Message):
    """Команда для быстрой покупки."""
    try:
        user_id = message.from_user.id
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            await message.answer("🛒 Ваша корзина пуста!")
            return
        
        total_price = sum(item["price"] * item["quantity"] for item in cart_items)
        
        await message.answer(
            f"💰 Оформление заказа\n\n"
            f"Сумма к оплате: {total_price} {settings.CURRENCY}\n\n"
            f"Выберите способ оплаты:",
            reply_markup=get_payment_methods_menu()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в команде buy: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
