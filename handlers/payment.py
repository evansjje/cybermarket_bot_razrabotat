from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from database import Database
from config import settings
from keyboards import main_menu_keyboard
from typing import Optional, Dict, Any, List
import logging

router = Router()
logger = logging.getLogger(__name__)

# Состояния для оплаты
class PaymentStates(StatesGroup):
    waiting_for_payment = State()
    processing_payment = State()

# Хранилище заказов (в реальном проекте лучше использовать БД)
order_storage: Dict[int, Dict[str, Any]] = {}

# Вспомогательная функция для создания заказа
async def create_order(db: Database, user_id: int, product_id: int) -> Optional[Dict[str, Any]]:
    """Создать заказ и вернуть его данные"""
    product = await db.get_product(product_id)
    if not product or not product.get("is_available", 1):
        return None
    
    order_data = {
        "order_id": None,
        "user_id": user_id,
        "product_id": product_id,
        "product_name": product["name"],
        "price": product["price"],
        "status": "pending",
        "payment_method": None,
        "file_path": product.get("file_path"),
        "download_link": product.get("download_link")
    }
    
    # Сохраняем заказ в БД
    order_id = await db.create_order(
        user_id=user_id,
        product_id=product_id,
        amount=product["price"],
        status="pending"
    )
    order_data["order_id"] = order_id
    
    # Сохраняем в хранилище
    if user_id not in order_storage:
        order_storage[user_id] = {}
    order_storage[user_id][order_id] = order_data
    
    return order_data

# Вспомогательная функция для отправки товара
async def deliver_product(message: Message, order_data: Dict[str, Any], db: Database):
    """Отправить товар пользователю после оплаты"""
    try:
        # Отправляем файл если есть
        if order_data.get("file_path"):
            try:
                with open(order_data["file_path"], "rb") as file:
                    await message.answer_document(
                        document=file,
                        caption=f"✅ Ваш товар: {order_data['product_name']}"
                    )
            except FileNotFoundError:
                # Если файл не найден, отправляем ссылку
                if order_data.get("download_link"):
                    await message.answer(
                        f"✅ Ваш товар: {order_data['product_name']}\n\n"
                        f"📥 Ссылка для скачивания: {order_data['download_link']}"
                    )
                else:
                    await message.answer(
                        f"✅ Ваш товар: {order_data['product_name']}\n\n"
                        f"⚠️ Файл временно недоступен. Обратитесь в поддержку."
                    )
        elif order_data.get("download_link"):
            await message.answer(
                f"✅ Ваш товар: {order_data['product_name']}\n\n"
                f"📥 Ссылка для скачивания: {order_data['download_link']}"
            )
        else:
            await message.answer(
                f"✅ Ваш товар: {order_data['product_name']}\n\n"
                f"📦 Товар будет отправлен в течение 5 минут."
            )
        
        # Обновляем статус заказа
        await db.update_order_status(order_data["order_id"], "completed")
        
    except Exception as e:
        logger.error(f"Ошибка при доставке товара: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при доставке товара. "
            "Пожалуйста, обратитесь в поддержку."
        )

# Обработчик оплаты через Telegram Payments
@router.callback_query(F.data.startswith("buy:"))
async def process_payment(callback: CallbackQuery, db: Database, state: FSMContext):
    """Начать процесс оплаты"""
    product_id = int(callback.data.split(":")[1])
    
    # Получаем товар
    product = await db.get_product(product_id)
    if not product or not product.get("is_available", 1):
        await callback.answer("Товар недоступен", show_alert=True)
        return
    
    # Создаем заказ
    order_data = await create_order(db, callback.from_user.id, product_id)
    if not order_data:
        await callback.answer("Не удалось создать заказ", show_alert=True)
        return
    
    # Создаем клавиатуру с выбором способа оплаты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Оплатить через Telegram",
                callback_data=f"pay_telegram:{order_data['order_id']}"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Оплатить через YooKassa",
                callback_data=f"pay_yookassa:{order_data['order_id']}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_payment"
            )
        ]
    ])
    
    await callback.message.edit_text(
        f"🧾 Заказ #{order_data['order_id']}\n\n"
        f"📦 Товар: {order_data['product_name']}\n"
        f"💰 Сумма: {order_data['price']}₽\n\n"
        f"Выберите способ оплаты:",
        reply_markup=keyboard
    )
    
    await state.set_state(PaymentStates.waiting_for_payment)

# Оплата через Telegram Payments
@router.callback_query(F.data.startswith("pay_telegram:"))
async def pay_via_telegram(callback: CallbackQuery, db: Database, state: FSMContext):
    """Оплата через Telegram Payments"""
    order_id = int(callback.data.split(":")[1])
    order_data = order_storage.get(callback.from_user.id, {}).get(order_id)
    
    if not order_data:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    # Отправляем счет на оплату
    await callback.message.answer_invoice(
        title=order_data["product_name"],
        description=f"Оплата заказа #{order_id}",
        payload=f"order_{order_id}",
        provider_token=settings.YOOKASSA_SECRET_KEY,  # Для Telegram Payments используем токен провайдера
        currency="RUB",
        prices=[
            LabeledPrice(
                label=order_data["product_name"],
                amount=int(order_data["price"] * 100)  # В копейках
            )
        ],
        start_parameter="cybermarket_payment"
    )
    
    await state.set_state(PaymentStates.processing_payment)

# Оплата через YooKassa
@router.callback_query(F.data.startswith("pay_yookassa:"))
async def pay_via_yookassa(callback: CallbackQuery, db: Database, state: FSMContext):
    """Оплата через YooKassa"""
    order_id = int(callback.data.split(":")[1])
    order_data = order_storage.get(callback.from_user.id, {}).get(order_id)
    
    if not order_data:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    try:
        import yookassa
        from uuid import uuid4
        
        # Настройка YooKassa
        yookassa.Configuration.account_id = settings.YOOKASSA_SHOP_ID
        yookassa.Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        
        # Создаем платеж
        payment = yookassa.Payment.create({
            "amount": {
                "value": f"{order_data['price']:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/your_bot_username"
            },
            "capture": True,
            "description": f"Оплата заказа #{order_id}",
            "metadata": {
                "order_id": str(order_id),
                "user_id": str(callback.from_user.id)
            }
        })
        
        # Сохраняем payment_id в заказе
        order_data["payment_id"] = payment.id
        
        # Отправляем ссылку на оплату
        confirmation_url = payment.confirmation.confirmation_url
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Перейти к оплате",
                    url=confirmation_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я оплатил",
                    callback_data=f"check_payment:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_payment"
                )
            ]
        ])
        
        await callback.message.edit_text(
            f"💳 Оплата через YooKassa\n\n"
            f"Заказ #{order_id}\n"
            f"Сумма: {order_data['price']}₽\n\n"
            f"Нажмите кнопку ниже для перехода к оплате:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании платежа YooKassa: {e}")
        await callback.answer(
            "Не удалось создать платеж. Попробуйте позже.",
            show_alert=True
        )

# Проверка статуса платежа YooKassa
@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment(callback: CallbackQuery, db: Database, state: FSMContext):
    """Проверить статус платежа"""
    order_id = int(callback.data.split(":")[1])
    order_data = order_storage.get(callback.from_user.id, {}).get(order_id)
    
    if not order_data:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    try:
        import yookassa
        
        # Настройка YooKassa
        yookassa.Configuration.account_id = settings.YOOKASSA_SHOP_ID
        yookassa.Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        
        # Получаем статус платежа
        payment = yookassa.Payment.find_one(order_data.get("payment_id"))
        
        if payment.status == "succeeded":
            # Платеж успешен
            await callback.answer("✅ Оплата подтверждена!", show_alert=True)
            
            # Доставляем товар
            await deliver_product(callback.message, order_data, db)
            
            # Обновляем баланс пользователя (реферальная программа)
            await db.update_user_balance(callback.from_user.id, order_data["price"])
            
            # Начисляем бонус рефереру если есть
            user = await db.get_user(callback.from_user.id)
            if user and user.get("referred_by"):
                bonus = order_data["price"] * 0.1  # 10% от суммы
                await db.update_user_balance(user["referred_by"], bonus)
            
            # Отправляем сообщение об успехе
            await callback.message.answer(
                "✅ Оплата прошла успешно!\n"
                "🎉 Спасибо за покупку!",
                reply_markup=main_menu_keyboard()
            )
            
            await state.clear()
            
        elif payment.status == "pending":
            await callback.answer(
                "⏳ Платеж еще не подтвержден. Попробуйте позже.",
                show_alert=True
            )
        else:
            await callback.answer(
                "❌ Платеж не прошел. Попробуйте еще раз.",
                show_alert=True
            )
            
    except Exception as e:
        logger.error(f"Ошибка при проверке платежа: {e}")
        await callback.answer(
            "Не удалось проверить платеж. Попробуйте позже.",
            show_alert=True
        )

# Обработчик предварительной проверки платежа
@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, db: Database):
    """Подтверждение предварительной проверки платежа"""
    try:
        # Проверяем заказ
        order_id = int(pre_checkout_query.invoice_payload.split("_")[1])
        user_id = pre_checkout_query.from_user.id
        
        order_data = order_storage.get(user_id, {}).get(order_id)
        if not order_data:
            await pre_checkout_query.answer(
                False,
                error_message="Заказ не найден"
            )
            return
        
        # Проверяем сумму
        expected_amount = int(order_data["price"] * 100)
        if pre_checkout_query.total_amount != expected_amount:
            await pre_checkout_query.answer(
                False,
                error_message="Сумма заказа изменилась"
            )
            return
        
        # Подтверждаем платеж
        await pre_checkout_query.answer(True)
        
    except Exception as e:
        logger.error(f"Ошибка при предварительной проверке: {e}")
        await pre_checkout_query.answer(
            False,
            error_message="Ошибка при обработке платежа"
        )

# Обработчик успешного платежа
@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, db: Database, state: FSMContext):
    """Обработка успешного платежа"""
    try:
        # Получаем данные платежа
        payment = message.successful_payment
        order_id = int(payment.invoice_payload.split("_")[1])
        user_id = message.from_user.id
        
        # Получаем заказ
        order_data = order_storage.get(user_id, {}).get(order_id)
        if not order_data:
            await message.answer(
                "❌ Заказ не найден. Обратитесь в поддержку.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        # Обновляем статус заказа
        await db.update_order_status(order_id, "paid")
        
        # Доставляем товар
        await deliver_product(message, order_data, db)
        
        # Обновляем баланс пользователя
        await db.update_user_balance(user_id, order_data["price"])
        
        # Начисляем бонус рефереру если есть
        user = await db.get_user(user_id)
        if user and user.get("referred_by"):
            bonus = order_data["price"] * 0.1  # 10% от суммы
            await db.update_user_balance(user["referred_by"], bonus)
        
        # Отправляем сообщение об успехе
        await message.answer(
            "✅ Оплата прошла успешно!\n"
            "🎉 Спасибо за покупку!",
            reply_markup=main_menu_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при обработке платежа. "
            "Обратитесь в поддержку.",
            reply_markup=main_menu_keyboard()
        )

# Отмена оплаты
@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отмена оплаты"""
    await callback.message.edit_text(
        "❌ Оплата отменена.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()

# Обработчик ошибок
@router.errors()
async def errors_handler(update: Update, exception: Exception):
    """Обработчик ошибок"""
    logger.error(f"Ошибка в payment.py: {exception}")
    return True
