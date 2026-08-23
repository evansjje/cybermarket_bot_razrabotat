import asyncio
import logging
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    SuccessfulPayment,
)

from config import settings
from database import Database
from keyboards import (
    get_payment_keyboard,
    get_product_keyboard,
    get_success_payment_keyboard,
)

logger = logging.getLogger(__name__)

router = Router(name="payment")


async def _get_product_by_id(db: Database, product_id: int) -> Optional[dict]:
    """Получить товар из БД по ID."""
    async with db._lock:
        async with db._conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ) as cursor:
            row = await cursor.fetchone()
    if row:
        return dict(row)
    return None


async def _get_user_by_id(db: Database, user_id: int) -> Optional[dict]:
    """Получить пользователя из БД по ID."""
    async with db._lock:
        async with db._conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
    if row:
        return dict(row)
    return None


async def _create_order(
    db: Database,
    user_id: int,
    product_id: int,
    amount: int,
    payment_method: str,
    status: str = "pending",
) -> int:
    """Создать заказ в БД и вернуть его ID."""
    async with db._lock:
        cursor = await db._conn.execute(
            """
            INSERT INTO orders (user_id, product_id, amount, payment_method, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, product_id, amount, payment_method, status),
        )
        await db._conn.commit()
        return cursor.lastrowid


async def _update_order_status(db: Database, order_id: int, status: str) -> None:
    """Обновить статус заказа."""
    async with db._lock:
        await db._conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await db._conn.commit()


async def _get_order_by_id(db: Database, order_id: int) -> Optional[dict]:
    """Получить заказ из БД по ID."""
    async with db._lock:
        async with db._conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
    if row:
        return dict(row)
    return None


async def _get_product_content(db: Database, product_id: int) -> Optional[str]:
    """Получить контент товара (файл/ссылка)."""
    product = await _get_product_by_id(db, product_id)
    if product:
        return product.get("content")
    return None


async def _send_product_to_user(
    bot: Bot, user_id: int, product: dict
) -> bool:
    """Отправить пользователю купленный товар."""
    try:
        content = product.get("content", "")
        if content.startswith("http"):
            await bot.send_message(
                user_id,
                f"🎉 Спасибо за покупку!\n\n📦 Ваш товар: {product['name']}\n\n🔗 Ссылка: {content}",
            )
        else:
            # Если это файл, отправляем как документ
            await bot.send_document(
                user_id,
                document=content,
                caption=f"🎉 Спасибо за покупку!\n\n📦 Ваш товар: {product['name']}",
            )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки товара пользователю {user_id}: {e}")
        return False


@router.callback_query(F.data.startswith("pay_"))
async def process_payment_callback(callback: CallbackQuery, bot: Bot, db: Database):
    """Обработка нажатия на кнопку оплаты."""
    product_id = int(callback.data.split("_")[1])
    product = await _get_product_by_id(db, product_id)

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    user = await _get_user_by_id(db, callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден. Нажмите /start", show_alert=True)
        return

    # Проверяем, есть ли у пользователя уже купленный товар
    async with db._lock:
        async with db._conn.execute(
            """
            SELECT * FROM orders 
            WHERE user_id = ? AND product_id = ? AND status = 'paid'
            """,
            (user["id"], product_id),
        ) as cursor:
            existing_order = await cursor.fetchone()

    if existing_order:
        await callback.answer("✅ Вы уже приобрели этот товар!", show_alert=True)
        # Отправляем товар повторно
        await _send_product_to_user(bot, callback.from_user.id, product)
        return

    # Создаём заказ
    order_id = await _create_order(
        db,
        user["id"],
        product_id,
        product["price"],
        "telegram",
    )

    # Формируем клавиатуру с кнопкой оплаты
    keyboard = get_payment_keyboard(product, order_id)

    await callback.message.edit_text(
        f"💳 Оплата товара: {product['name']}\n"
        f"💰 Цена: {product['price']} ₽\n\n"
        f"Нажмите кнопку ниже для оплаты:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_payment_"))
async def process_confirm_payment(callback: CallbackQuery, bot: Bot, db: Database):
    """Подтверждение оплаты через Telegram Payments."""
    order_id = int(callback.data.split("_")[2])
    order = await _get_order_by_id(db, order_id)

    if not order:
        await callback.answer("❌ Заказ не найден.", show_alert=True)
        return

    product = await _get_product_by_id(db, order["product_id"])
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    # Проверяем, настроен ли Telegram Payments
    if not settings.PAYMENT_TOKEN or settings.PAYMENT_TOKEN == "YOUR_PAYMENT_TOKEN":
        # Если нет токена, используем YooKassa или заглушку
        await callback.answer(
            "⚠️ Оплата временно недоступна. Пожалуйста, попробуйте позже.",
            show_alert=True,
        )
        return

    # Создаём счёт через Telegram Payments
    prices = [LabeledPrice(label=product["name"], amount=product["price"] * 100)]

    try:
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=product["name"],
            description=product.get("description", "Цифровой товар"),
            payload=f"order_{order_id}",
            provider_token=settings.PAYMENT_TOKEN,
            currency="RUB",
            prices=prices,
            reply_markup=get_success_payment_keyboard(),
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка создания счёта: {e}")
        await callback.answer(
            "❌ Не удалось создать счёт. Попробуйте позже.",
            show_alert=True,
        )


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    """Обработка предварительной проверки оплаты."""
    try:
        # Проверяем, что заказ существует
        order_id = int(pre_checkout_query.invoice_payload.split("_")[1])
        # Здесь можно добавить дополнительную валидацию
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        logger.error(f"Ошибка pre_checkout: {e}")
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Не удалось обработать платёж. Попробуйте ещё раз.",
        )


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, bot: Bot, db: Database):
    """Обработка успешной оплаты."""
    payment: SuccessfulPayment = message.successful_payment

    try:
        order_id = int(payment.invoice_payload.split("_")[1])
        order = await _get_order_by_id(db, order_id)

        if not order:
            await message.answer("❌ Заказ не найден. Обратитесь в поддержку.")
            return

        # Обновляем статус заказа
        await _update_order_status(db, order_id, "paid")

        # Получаем товар
        product = await _get_product_by_id(db, order["product_id"])
        if not product:
            await message.answer("❌ Товар не найден. Обратитесь в поддержку.")
            return

        # Отправляем товар пользователю
        success = await _send_product_to_user(bot, message.from_user.id, product)

        if success:
            await message.answer(
                "✅ Оплата прошла успешно!\n"
                "📦 Товар отправлен вам в чат.\n"
                "Спасибо за покупку! 🎉",
                reply_markup=get_success_payment_keyboard(),
            )
        else:
            await message.answer(
                "⚠️ Оплата прошла, но не удалось отправить товар.\n"
                "Пожалуйста, обратитесь в поддержку.",
            )

    except Exception as e:
        logger.error(f"Ошибка обработки успешной оплаты: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке оплаты.\n"
            "Пожалуйста, обратитесь в поддержку."
        )


@router.callback_query(F.data.startswith("yookassa_"))
async def process_yookassa_payment(callback: CallbackQuery, bot: Bot, db: Database):
    """Обработка оплаты через YooKassa."""
    order_id = int(callback.data.split("_")[1])
    order = await _get_order_by_id(db, order_id)

    if not order:
        await callback.answer("❌ Заказ не найден.", show_alert=True)
        return

    product = await _get_product_by_id(db, order["product_id"])
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    # Проверяем, настроен ли YooKassa
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        await callback.answer(
            "⚠️ Оплата через YooKassa временно недоступна.\n"
            "Пожалуйста, используйте Telegram Payments.",
            show_alert=True,
        )
        return

    # Здесь должна быть интеграция с YooKassa API
    # Для примера просто отправляем сообщение
    await callback.message.answer(
        f"💳 Оплата через YooKassa\n\n"
        f"Товар: {product['name']}\n"
        f"Цена: {product['price']} ₽\n\n"
        f"Для оплаты перейдите по ссылке:\n"
        f"https://yoomoney.ru/checkout/payments/v2?orderId={order_id}",
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_payment")
async def process_cancel_payment(callback: CallbackQuery, bot: Bot, db: Database):
    """Отмена оплаты."""
    await callback.message.edit_text(
        "❌ Оплата отменена.\n"
        "Если у вас возникли вопросы, обратитесь в поддержку.",
    )
    await callback.answer()


@router.message(Command("my_orders"))
async def cmd_my_orders(message: Message, db: Database):
    """Показать заказы пользователя."""
    user = await _get_user_by_id(db, message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден. Нажмите /start")
        return

    async with db._lock:
        async with db._conn.execute(
            """
            SELECT o.*, p.name as product_name, p.price as product_price
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
            """,
            (user["id"],),
        ) as cursor:
            orders = await cursor.fetchall()

    if not orders:
        await message.answer("📭 У вас пока нет заказов.")
        return

    text = "📋 Ваши заказы:\n\n"
    for order in orders:
        status_text = {
            "pending": "⏳ Ожидает оплаты",
            "paid": "✅ Оплачен",
            "cancelled": "❌ Отменён",
        }.get(order["status"], order["status"])

        text += (
            f"📦 {order['product_name']}\n"
            f"💰 {order['product_price']} ₽\n"
            f"📊 Статус: {status_text}\n"
            f"🕐 {order['created_at']}\n\n"
        )

    await message.answer(text)


@router.callback_query(F.data.startswith("repurchase_"))
async def process_repurchase(callback: CallbackQuery, bot: Bot, db: Database):
    """Повторная покупка товара."""
    product_id = int(callback.data.split("_")[1])
    product = await _get_product_by_id(db, product_id)

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    # Отправляем товар повторно
    success = await _send_product_to_user(bot, callback.from_user.id, product)

    if success:
        await callback.answer("✅ Товар отправлен повторно!", show_alert=True)
    else:
        await callback.answer("❌ Не удалось отправить товар.", show_alert=True)
