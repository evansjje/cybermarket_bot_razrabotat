# handlers/payment.py
import asyncio
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from config import settings
from database import Database
from keyboards import main_menu_keyboard, product_detail_keyboard

router = Router()
db = Database()

# YooKassa
try:
    from yookassa import Configuration, Payment as YooKassaPayment
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
    YOOKASSA_ENABLED = True
except ImportError:
    YOOKASSA_ENABLED = False
    logging.warning("YooKassa не установлен. Оплата через YooKassa отключена.")


class PaymentStates(StatesGroup):
    waiting_for_payment_method = State()


async def create_yookassa_payment(amount: float, description: str, user_id: int) -> Optional[str]:
    """Создать платёж через YooKassa и вернуть URL для оплаты"""
    if not YOOKASSA_ENABLED:
        return None
    
    try:
        payment = YooKassaPayment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/YourBotUsername"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id)
            }
        })
        return payment.confirmation.confirmation_url
    except Exception as e:
        logging.error(f"YooKassa payment creation error: {e}")
        return None


async def check_yookassa_payment(payment_id: str) -> bool:
    """Проверить статус платежа YooKassa"""
    if not YOOKASSA_ENABLED:
        return False
    
    try:
        payment = YooKassaPayment.find_one(payment_id)
        return payment.status == "succeeded"
    except Exception as e:
        logging.error(f"YooKassa payment check error: {e}")
        return False


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery, state: FSMContext):
    """Начать процесс оплаты товара"""
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    if not product.get("is_active", 1):
        await callback.answer("Товар недоступен", show_alert=True)
        return
    
    # Сохраняем данные о покупке
    await state.update_data(
        product_id=product_id,
        product_name=product["name"],
        product_price=product["price"],
        product_content=product.get("content"),
        product_file_path=product.get("file_path")
    )
    
    # Показываем выбор способа оплаты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить картой (YooKassa)", callback_data="pay:yookassa")],
        [InlineKeyboardButton(text="⚡️ Telegram Stars", callback_data="pay:telegram")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"product:{product_id}")]
    ])
    
    await callback.message.edit_text(
        f"💳 Выберите способ оплаты для товара «{product['name']}»\n"
        f"💰 Цена: {product['price']}₽",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay:"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    """Обработка выбранного способа оплаты"""
    payment_method = callback.data.split(":", 1)[1]
    data = await state.get_data()
    
    if not data:
        await callback.answer("Сессия истекла. Попробуйте снова.", show_alert=True)
        return
    
    product_id = data.get("product_id")
    product_name = data.get("product_name")
    product_price = data.get("product_price")
    
    if payment_method == "yookassa":
        # YooKassa оплата
        payment_url = await create_yookassa_payment(
            amount=product_price,
            description=f"Покупка: {product_name}",
            user_id=callback.from_user.id
        )
        
        if payment_url:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url)],
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm:yookassa")],
                [InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_payment")]
            ])
            
            await callback.message.edit_text(
                f"💳 Оплата через YooKassa\n\n"
                f"Товар: {product_name}\n"
                f"Сумма: {product_price}₽\n\n"
                f"Нажмите кнопку для перехода к оплате.",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при создании платежа. Попробуйте позже.",
                reply_markup=main_menu_keyboard()
            )
    
    elif payment_method == "telegram":
        # Telegram Payments (Stars)
        if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            await callback.message.edit_text(
                "❌ Telegram Payments не настроены. Используйте YooKassa.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        # Отправляем инвойс
        await callback.message.delete()
        await callback.message.answer_invoice(
            title=product_name,
            description=f"Цифровой товар: {product_name}",
            payload=f"product_{product_id}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=product_name, amount=product_price)],
            provider_token=""
        )
    
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение предварительной проверки платежа"""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    """Обработка успешного платежа через Telegram Payments"""
    payment_info = message.successful_payment
    product_id = int(payment_info.invoice_payload.split("_")[1])
    
    product = await db.get_product(product_id)
    if not product:
        await message.answer("❌ Товар не найден")
        return
    
    # Создаём заказ в БД
    order_id = await db.create_order(
        user_id=message.from_user.id,
        product_id=product_id,
        amount=product["price"],
        payment_method="telegram_stars"
    )
    
    # Выдаём товар
    await deliver_product(message, product, order_id)
    
    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data.startswith("confirm:"))
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    """Подтверждение оплаты через YooKassa"""
    payment_method = callback.data.split(":", 1)[1]
    data = await state.get_data()
    
    if not data:
        await callback.answer("Сессия истекла", show_alert=True)
        return
    
    product_id = data.get("product_id")
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Проверяем платеж (в реальном проекте нужно проверить через API YooKassa)
    # Здесь упрощённая проверка - в реальном проекте нужно хранить payment_id и проверять его статус
    
    # Создаём заказ
    order_id = await db.create_order(
        user_id=callback.from_user.id,
        product_id=product_id,
        amount=product["price"],
        payment_method="yookassa"
    )
    
    # Выдаём товар
    await deliver_product(callback.message, product, order_id)
    
    # Очищаем состояние
    await state.clear()
    await callback.answer("✅ Оплата подтверждена")


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отмена оплаты"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Оплата отменена.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


async def deliver_product(message: Message, product: dict, order_id: int):
    """Выдача цифрового товара после оплаты"""
    # Отправляем подтверждение
    await message.answer(
        f"✅ Оплата прошла успешно!\n"
        f"📦 Заказ #{order_id}\n"
        f"🎁 Товар: {product['name']}\n\n"
        f"Спасибо за покупку!"
    )
    
    # Выдаём файл, если есть
    if product.get("file_path"):
        try:
            with open(product["file_path"], "rb") as file:
                await message.answer_document(
                    document=file,
                    caption=f"📦 Ваш товар: {product['name']}"
                )
        except FileNotFoundError:
            await message.answer("❌ Файл товара не найден. Обратитесь в поддержку.")
        except Exception as e:
            logging.error(f"Error sending file: {e}")
            await message.answer("❌ Ошибка при отправке файла. Обратитесь в поддержку.")
    
    # Выдаём контент (текст/ссылку)
    if product.get("content"):
        await message.answer(
            f"🔗 Ваш доступ к товару:\n\n{product['content']}"
        )
    
    # Если нет ни файла, ни контента
    if not product.get("file_path") and not product.get("content"):
        await message.answer(
            "ℹ️ Товар будет доставлен в течение 5 минут.\n"
            "Если этого не произошло - обратитесь в поддержку."
        )
