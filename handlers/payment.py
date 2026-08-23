from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import main_menu_kb, payment_kb, success_kb
from config import settings
import yookassa
from yookassa import Payment

router = Router()
db = Database()

yookassa.Configuration.account_id = settings.YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


class PaymentStates(StatesGroup):
    waiting_for_payment = State()


@router.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден")
        return

    user_id = callback.from_user.id
    if order[2] != user_id:
        await callback.answer("Это не ваш заказ")
        return

    # Create YooKassa payment
    payment = Payment.create({
        "amount": {
            "value": f"{order[3]:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"
        },
        "capture": True,
        "description": f"Заказ #{order_id}",
        "metadata": {
            "order_id": order_id,
            "user_id": user_id
        }
    })

    await db.update_order_payment_id(order_id, payment.id)
    await callback.message.edit_text(
        f"💳 Оплата заказа #{order_id}\n\n"
        f"Сумма: {order[3]} руб.\n\n"
        f"Нажмите кнопку для оплаты:",
        reply_markup=payment_kb(payment.confirmation.confirmation_url, order_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("check_"))
async def check_payment(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден")
        return

    payment = Payment.find_one(order[5])
    if payment.status == "succeeded":
        # Payment successful
        await db.update_order_status(order_id, "paid")
        product = await db.get_product(order[4])
        
        # Deliver product content
        if product[5]:  # file_path
            await callback.message.answer_document(
                document=product[5],
                caption=f"✅ Оплата получена!\n\n📦 {product[1]}\n\nСпасибо за покупку!"
            )
        elif product[6]:  # download_link
            await callback.message.answer(
                f"✅ Оплата получена!\n\n📦 {product[1]}\n\n"
                f"🔗 Ссылка для скачивания: {product[6]}",
                reply_markup=success_kb()
            )
        else:
            await callback.message.answer(
                f"✅ Оплата получена!\n\n📦 {product[1]}\n\n"
                f"📄 {product[2]}",
                reply_markup=success_kb()
            )
        
        # Add referral bonus if applicable
        user = await db.get_user(callback.from_user.id)
        if user and user[6]:  # referred_by
            referrer = await db.get_user(user[6])
            if referrer:
                bonus = order[3] * 0.1  # 10% bonus
                await db.update_balance(referrer[0], bonus)
                await db.add_referral_bonus(referrer[0], bonus)
        
        await callback.message.answer("🎉 Спасибо за покупку!", reply_markup=main_menu_kb())
    elif payment.status == "canceled":
        await callback.answer("❌ Платеж отменен")
    else:
        await callback.answer("⏳ Платеж еще не подтвержден", show_alert=True)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment_info = message.successful_payment
    order_id = int(payment_info.invoice_payload)
    await db.update_order_status(order_id, "paid")
    
    order = await db.get_order(order_id)
    if order:
        product = await db.get_product(order[4])
        if product[5]:
            await message.answer_document(
                document=product[5],
                caption=f"✅ Оплата получена!\n\n📦 {product[1]}"
            )
        elif product[6]:
            await message.answer(
                f"✅ Оплата получена!\n\n📦 {product[1]}\n\n"
                f"🔗 Ссылка: {product[6]}"
            )
        else:
            await message.answer(
                f"✅ Оплата получена!\n\n📦 {product[1]}\n\n📄 {product[2]}"
            )
    
    await message.answer("🎉 Спасибо за покупку!", reply_markup=main_menu_kb())


@router.callback_query(F.data == "payment_success")
async def payment_success(callback: CallbackQuery):
    await callback.message.edit_text(
        "✅ Оплата успешно подтверждена!\n\n"
        "Товар будет доставлен автоматически.",
        reply_markup=main_menu_kb()
    )
    await callback.answer()
