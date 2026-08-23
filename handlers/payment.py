Вот исправленный код файла `handlers/payment.py`:

```python
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from config import settings
from database import db
from keyboards import (
    get_payment_methods_keyboard,
    get_payment_confirmation_keyboard,
    get_main_menu,
    get_product_detail_keyboard
)

# Попытка импорта YooKassa (необязательный)
try:
    from yookassa import Configuration, Payment as YooKassaPayment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False

router = Router()
logger = logging.getLogger(__name__)


class PaymentStates(StatesGroup):
    """Состояния для процесса оплаты."""
    choosing_method = State()
    confirming_payment = State()
    waiting_for_delivery = State()


async def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Получает товар по ID из базы данных."""
    try:
        product = await db.get_product(product_id)
        return product
    except Exception as e:
        logger.error(f"Ошибка получения товара {product_id}: {e}")
        return None


async def create_order(user_id: int, product_id: int, amount: float) -> Optional[int]:
    """Создает заказ в базе данных."""
    try:
        order_id = await db.create_order(
            user_id=user_id,
            product_id=product_id,
            amount=amount,
            status="pending"
        )
        return order_id
    except Exception as e:
        logger.error(f"Ошибка создания заказа: {e}")
        return None


async def update_order_status(order_id: int, status: str, payment_id: Optional[str] = None) -> bool:
    """Обновляет статус заказа."""
    try:
        await db.update_order_status(order_id, status, payment_id)
        return True
    except Exception as e:
        logger.error(f"Ошибка обновления статуса заказа {order_id}: {e}")
        return False


async def deliver_product(order_id: int, user_id: int, product_id: int) -> bool:
    """Выдает товар пользователю после успешной оплаты."""
    try:
        product = await get_product_by_id(product_id)
        if not product:
            return False

        # Получаем данные для доставки
        delivery_data = product.get("delivery_data", {})
        
        # Отправляем сообщение с товаром
        from aiogram import Bot
        bot = Bot.get_current()
        
        # Формируем сообщение с товаром
        message_text = (
            f"✅ Оплата подтверждена!\n\n"
            f"📦 Ваш товар: {product['name']}\n"
            f"💰 Сумма: {product['price']}₽\n\n"
        )
        
        # Если есть файл - отправляем файл
        if product.get("file_path"):
            try:
                with open(product["file_path"], "rb") as file:
                    await bot.send_document(
                        chat_id=user_id,
                        document=file,
                        caption=f"📦 {product['name']}\n\nСпасибо за покупку!"
                    )
            except FileNotFoundError:
                message_text += "⚠️ Файл временно недоступен. Обратитесь в поддержку."
        
        # Если есть ссылка - отправляем ссылку
        if product.get("download_link"):
            message_text += f"🔗 Ссылка для скачивания: {product['download_link']}\n"
        
        # Если есть дополнительная информация
        if product.get("description"):
            message_text += f"\n📝 Описание: {product['description']}\n"
        
        # Отправляем текстовое сообщение
        await bot.send_message(
            chat_id=user_id,
            text=message_text,
            reply_markup=get_main_menu()
        )
        
        # Обновляем статус заказа
        await update_order_status(order_id, "completed")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка доставки товара: {e}")
        return False


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery, state: FSMContext):
    """Начало процесса покупки."""
    product_id = int(callback.data.split(":", 1)[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    # Сохраняем данные о покупке
    await state.update_data(
        product_id=product_id,
        product_name=product["name"],
        product_price=product["price"]
    )
    
    # Показываем выбор способа оплаты
    await callback.message.edit_text(
        f"💳 Вы выбрали: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n\n"
        f"Выберите способ оплаты:",
        reply_markup=get_payment_methods_keyboard()
    )
    
    await state.set_state(PaymentStates.choosing_method)
    await callback.answer()


@router.callback_query(F.data == "pay_yookassa")
async def pay_with_yookassa(callback: CallbackQuery, state: FSMContext):
    """Оплата через YooKassa."""
    if not YOOKASSA_AVAILABLE:
        await callback.answer("❌ YooKassa не настроена", show_alert=True)
        return
    
    data = await state.get_data()
    product_id = data.get("product_id")
    product_price = data.get("product_price")
    
    if not product_id or not product_price:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    # Создаем заказ
    order_id = await create_order(callback.from_user.id, product_id, product_price)
    if not order_id:
        await callback.answer("❌ Не удалось создать заказ", show_alert=True)
        return
    
    try:
        # Настройка YooKassa
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.yookassa_secret_key
        
        # Создание платежа
        payment = YooKassaPayment.create({
            "amount": {
                "value": f"{product_price:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{callback.bot.username}"
            },
            "capture": True,
            "description": f"Заказ #{order_id}",
            "metadata": {
                "order_id": str(order_id),
                "user_id": str(callback.from_user.id)
            }
        })
        
        # Сохраняем payment_id
        await state.update_data(
            order_id=order_id,
            payment_id=payment.id
        )
        
        # Отправляем ссылку на оплату
        confirmation_url = payment.confirmation.confirmation_url
        await callback.message.edit_text(
            f"💳 Оплата через YooKassa\n\n"
            f"📦 Заказ: #{order_id}\n"
            f"💰 Сумма: {product_price}₽\n\n"
            f"Для оплаты перейдите по ссылке:\n"
            f"{confirmation_url}\n\n"
            f"После оплаты нажмите кнопку ниже:",
            reply_markup=get_payment_confirmation_keyboard()
        )
        
        await state.set_state(PaymentStates.confirming_payment)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка YooKassa: {e}")
        await callback.answer("❌ Ошибка при создании платежа", show_alert=True)


@router.callback_query(F.data == "pay_telegram")
async def pay_with_telegram(callback: CallbackQuery, state: FSMContext):
    """Оплата через Telegram Payments."""
    if not settings.TELEGRAM_PAYMENT_TOKEN or settings.TELEGRAM_PAYMENT_TOKEN.get_secret_value() == "YOUR_TELEGRAM_PAYMENT_TOKEN":
        await callback.answer("❌ Telegram Payments не настроен", show_alert=True)
        return
    
    data = await state.get_data()
    product_id = data.get("product_id")
    product_name = data.get("product_name")
    product_price = data.get("product_price")
    
    if not product_id or not product_price:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    # Создаем заказ
    order_id = await create_order(callback.from_user.id, product_id, product_price)
    if not order_id:
        await callback.answer("❌ Не удалось создать заказ", show_alert=True)
        return
    
    # Отправляем счет
    prices = [LabeledPrice(label=product_name, amount=int(product_price * 100))]
    
    try:
        await callback.message.answer_invoice(
            title=f"Покупка: {product_name}",
            description=f"Заказ #{order_id}",
            payload=f"order_{order_id}",
            provider_token=settings.TELEGRAM_PAYMENT_TOKEN.get_secret_value(),
            currency="rub",
            prices=prices,
            start_parameter="cybermarket"
        )
        
        await state.update_data(order_id=order_id)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка Telegram Payments: {e}")
        await callback.answer("❌ Ошибка при создании счета", show_alert=True)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Обработка предварительной проверки платежа."""
    await pre_checkout_query.answer(ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment_handler(message: Message, state: FSMContext):
    """Обработка успешного платежа."""
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    
    # Извлекаем order_id из payload
    try:
        order_id = int(payload.split("_")[1])
    except (IndexError, ValueError):
        await message.answer("❌ Ошибка обработки платежа")
        return
    
    # Получаем данные из state
    data = await state.get_data()
    product_id = data.get("product_id")
    
    if not product_id:
        # Если нет в state, ищем в заказе
        order = await db.get_order(order_id)
        if order:
            product_id = order["product_id"]
    
    # Доставляем товар
    success = await deliver_product(order_id, message.from_user.id, product_id)
    
    if success:
        await message.answer(
            "🎉 Оплата прошла успешно!\n"
            "Товар отправлен вам в чат.",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при доставке товара.\n"
            "Пожалуйста, обратитесь в поддержку.",
            reply_markup=get_main_menu()
        )
    
    await state.clear()


@router.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    """Подтверждение оплаты (для YooKassa)."""
    data = await state.get_data()
    order_id = data.get("order_id")
    payment_id = data.get("payment_id")
    product_id = data.get("product_id")
    
    if not order_id:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Проверяем статус платежа в YooKassa
    if YOOKASSA_AVAILABLE and payment_id:
        try:
            Configuration.account_id = settings.YOOKASSA_SHOP_ID
            Configuration.secret_key = settings.yookassa_secret_key
            
            payment = YooKassaPayment.find_one(payment_id)
            
            if payment.status == "succeeded":
                # Платеж успешен
                success = await deliver_product(order_id, callback.from_user.id, product_id)
                
                if success:
                    await callback.message.edit_text(
                        "✅ Оплата подтверждена!\n"
                        "Товар отправлен вам в чат.",
                        reply_markup=get_main_menu()
                    )
                else:
                    await callback.message.edit_text(
                        "❌ Ошибка доставки товара.\n"
                        "Обратитесь в поддержку.",
                        reply_markup=get_main_menu()
                    )
                
                await state.clear()
                await callback.answer()
                return
            elif payment.status == "canceled":
                await callback.message.edit_text(
                    "❌ Платеж был отменен.",
                    reply_markup=get_main_menu()
                )
                await state.clear()
                await callback.answer()
                return
            else:
                await callback.answer("⏳ Платеж еще не подтвержден", show_alert=True)
                return
                
        except Exception as e:
            logger.error(f"Ошибка проверки платежа YooKassa: {e}")
            await callback.answer("❌ Ошибка проверки платежа", show_alert=True)
            return
    
    await callback.answer("❌ Способ оплаты не поддерживается", show_alert=True)


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отмена оплаты."""
    data = await state.get_data()
    order_id = data.get("order_id")
    
    if order_id:
        await update_order_status(order_id, "cancelled")
    
    await state.clear()
    await callback.message.edit_text(
        "❌ Оплата отменена.",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_product")
async def back_to_product(callback: CallbackQuery, state: FSMContext):
    """Возврат к товару."""
    data = await state.get_data()
    product_id = data.get("product_id")
    
    if product_id:
        product = await get_product_by_id(product_id)
        if product:
            await callback.message.edit_text(
                f"📦 {product['name']}\n"
                f"💰 Цена: {product['price']}₽\n\n"
                f"{product.get('description', '')}",
                reply_markup=get_product_detail_keyboard(product_id)
            )
    
    await state.clear()
    await callback.answer()
```

**Что было исправлено:**

Ошибка была в функции `back_to_product`. В вызове `await callback.message.edit_text(...)` не хватало закрывающей скобки `)` для метода `edit_text`. Я добавил недостающую скобку в конце вызова:

```python
await callback.message.edit_text(
    f"📦 {product['name']}\n"
    f"💰 Цена: {product['price']}₽\n\n"
    f"{product.get('description', '')}",
    reply_markup=get_product_detail_keyboard(product_id)
)  # <-- Здесь была добавлена закрывающая скобка
```

Теперь код синтаксически корректен и готов к использованию.
