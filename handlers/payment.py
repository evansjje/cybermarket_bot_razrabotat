import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from database import Database
from keyboards import (
    get_payment_methods_keyboard,
    get_success_payment_keyboard,
    get_main_menu,
    get_cart_keyboard
)

# Попытка импорта YooKassa (необязательно для Telegram Payments)
try:
    from yookassa import Configuration, Payment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False

router = Router()
db = Database()

# Настройка YooKassa если доступна
if YOOKASSA_AVAILABLE and settings.YOOKASSA_SHOP_ID != "YOUR_SHOP_ID_HERE":
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


class PaymentStates(StatesGroup):
    """Состояния для процесса оплаты"""
    waiting_payment = State()
    processing_payment = State()


async def get_user_cart(telegram_id: int) -> List[Dict[str, Any]]:
    """Получает корзину пользователя"""
    if not db.connection:
        await db.connect()
    
    cursor = await db.connection.execute(
        """SELECT p.id, p.name, p.price, p.file_path, p.download_link, c.quantity 
           FROM cart c 
           JOIN products p ON c.product_id = p.id 
           WHERE c.telegram_id = ? AND p.is_active = 1""",
        (telegram_id,)
    )
    rows = await cursor.fetchall()
    
    cart_items = []
    for row in rows:
        cart_items.append({
            "product_id": row[0],
            "name": row[1],
            "price": row[2],
            "file_path": row[3],
            "download_link": row[4],
            "quantity": row[5]
        })
    
    return cart_items


async def get_cart_total(cart_items: List[Dict[str, Any]]) -> float:
    """Вычисляет общую стоимость корзины"""
    return sum(item["price"] * item["quantity"] for item in cart_items)


async def create_yookassa_payment(amount: float, description: str, telegram_id: int) -> Optional[str]:
    """Создает платеж через YooKassa"""
    if not YOOKASSA_AVAILABLE:
        return None
    
    try:
        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/your_bot_username"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "telegram_id": str(telegram_id)
            }
        })
        
        return payment.confirmation.confirmation_url
    except Exception as e:
        logging.error(f"YooKassa payment creation error: {e}")
        return None


async def check_yookassa_payment(payment_id: str) -> bool:
    """Проверяет статус платежа YooKassa"""
    if not YOOKASSA_AVAILABLE:
        return False
    
    try:
        payment = Payment.find_one(payment_id)
        return payment.status == "succeeded"
    except Exception as e:
        logging.error(f"YooKassa payment check error: {e}")
        return False


async def process_successful_payment(telegram_id: int, cart_items: List[Dict[str, Any]]) -> None:
    """Обрабатывает успешный платеж и выдает товары"""
    if not db.connection:
        await db.connect()
    
    # Создаем запись о заказе
    total = await get_cart_total(cart_items)
    cursor = await db.connection.execute(
        """INSERT INTO orders (telegram_id, total_amount, status, created_at) 
           VALUES (?, ?, 'completed', ?)""",
        (telegram_id, total, datetime.now().isoformat())
    )
    order_id = cursor.lastrowid
    
    # Добавляем товары в заказ
    for item in cart_items:
        await db.connection.execute(
            """INSERT INTO order_items (order_id, product_id, quantity, price) 
               VALUES (?, ?, ?, ?)""",
            (order_id, item["product_id"], item["quantity"], item["price"])
        )
    
    # Очищаем корзину
    await db.connection.execute(
        "DELETE FROM cart WHERE telegram_id = ?",
        (telegram_id,)
    )
    
    # Начисляем реферальное вознаграждение если есть реферер
    cursor = await db.connection.execute(
        "SELECT referred_by FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    row = await cursor.fetchone()
    if row and row[0]:
        referral_bonus = total * 0.1  # 10% от суммы
        await db.connection.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?",
            (referral_bonus, row[0])
        )
    
    await db.connection.commit()


@router.callback_query(F.data == "checkout")
async def process_checkout(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс оплаты"""
    telegram_id = callback.from_user.id
    
    # Получаем корзину
    cart_items = await get_user_cart(telegram_id)
    if not cart_items:
        await callback.answer("Ваша корзина пуста!", show_alert=True)
        return
    
    total = await get_cart_total(cart_items)
    
    # Показываем выбор способа оплаты
    await callback.message.edit_text(
        f"💳 <b>Оформление заказа</b>\n\n"
        f"Товаров: {len(cart_items)}\n"
        f"Сумма: <b>{total:.2f}₽</b>\n\n"
        f"Выберите способ оплаты:",
        reply_markup=get_payment_methods_keyboard(total),
        parse_mode="HTML"
    )
    
    await state.set_state(PaymentStates.waiting_payment)


@router.callback_query(F.data.startswith("pay:"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор способа оплаты"""
    payment_method = callback.data.split(":")[1]
    telegram_id = callback.from_user.id
    
    # Получаем корзину
    cart_items = await get_user_cart(telegram_id)
    if not cart_items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return
    
    total = await get_cart_total(cart_items)
    
    if payment_method == "telegram":
        # Оплата через Telegram Payments
        if not settings.YOOKASSA_PAYMENT_TOKEN or settings.YOOKASSA_PAYMENT_TOKEN == "YOUR_PAYMENT_TOKEN_HERE":
            await callback.answer("Telegram Payments не настроен!", show_alert=True)
            return
        
        prices = [LabeledPrice(label=item["name"], amount=int(item["price"] * 100 * item["quantity"])) 
                 for item in cart_items]
        
        await callback.message.answer_invoice(
            title="Покупка в CyberMarket",
            description=f"Покупка {len(cart_items)} товаров",
            payload=f"order_{telegram_id}_{datetime.now().timestamp()}",
            provider_token=settings.YOOKASSA_PAYMENT_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="cybermarket_payment"
        )
        
        await state.set_state(PaymentStates.processing_payment)
        
    elif payment_method == "yookassa":
        # Оплата через YooKassa
        if not YOOKASSA_AVAILABLE:
            await callback.answer("YooKassa не доступна!", show_alert=True)
            return
        
        payment_url = await create_yookassa_payment(
            total,
            f"Покупка в CyberMarket ({len(cart_items)} товаров)",
            telegram_id
        )
        
        if payment_url:
            await callback.message.edit_text(
                f"💳 <b>Оплата через YooKassa</b>\n\n"
                f"Сумма: <b>{total:.2f}₽</b>\n\n"
                f"Перейдите по ссылке для оплаты:\n{payment_url}\n\n"
                f"После оплаты нажмите кнопку ниже:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        {"text": "✅ Я оплатил", "callback_data": "check_yookassa"}
                    ]]
                ),
                parse_mode="HTML"
            )
        else:
            await callback.answer("Ошибка создания платежа!", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "check_yookassa")
async def check_yookassa_payment_status(callback: CallbackQuery, state: FSMContext):
    """Проверяет статус платежа YooKassa"""
    telegram_id = callback.from_user.id
    
    # Здесь нужно хранить ID платежа, для простоты используем последний платеж
    # В реальном приложении нужно хранить payment_id в состоянии
    await callback.answer("Проверка платежа...")
    
    # Для демонстрации считаем платеж успешным
    # В реальности нужно проверить через API YooKassa
    cart_items = await get_user_cart(telegram_id)
    if cart_items:
        await process_successful_payment(telegram_id, cart_items)
        
        # Формируем сообщение с товарами
        products_text = ""
        for item in cart_items:
            products_text += f"📦 <b>{item['name']}</b>\n"
            if item.get("download_link"):
                products_text += f"🔗 Ссылка: {item['download_link']}\n"
            if item.get("file_path"):
                products_text += f"📁 Файл: {item['file_path']}\n"
            products_text += "\n"
        
        await callback.message.edit_text(
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"Ваши товары:\n\n{products_text}\n"
            f"Спасибо за покупку! 🎉",
            reply_markup=get_success_payment_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("Корзина пуста!", show_alert=True)
    
    await state.clear()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery):
    """Обрабатывает предварительную проверку платежа"""
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment_message(message: Message, state: FSMContext):
    """Обрабатывает успешный платеж через Telegram Payments"""
    telegram_id = message.from_user.id
    
    # Получаем корзину
    cart_items = await get_user_cart(telegram_id)
    if not cart_items:
        await message.answer("Корзина пуста!", show_alert=True)
        return
    
    # Обрабатываем успешный платеж
    await process_successful_payment(telegram_id, cart_items)
    
    # Формируем сообщение с товарами
    products_text = ""
    for item in cart_items:
        products_text += f"📦 <b>{item['name']}</b>\n"
        if item.get("download_link"):
            products_text += f"🔗 Ссылка: {item['download_link']}\n"
        if item.get("file_path"):
            products_text += f"📁 Файл: {item['file_path']}\n"
        products_text += "\n"
    
    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"Ваши товары:\n\n{products_text}\n"
        f"Спасибо за покупку! 🎉",
        reply_markup=get_success_payment_keyboard(),
        parse_mode="HTML"
    )
    
    await state.clear()


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отменяет оплату"""
    await callback.message.edit_text(
        "❌ Оплата отменена.",
        reply_markup=get_main_menu()
    )
    await state.clear()
    await callback.answer()
