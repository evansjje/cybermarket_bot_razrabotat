# handlers/payment.py
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from database import Database
from keyboards import main_menu_kb
from config import settings

router = Router()
db = Database()
logger = logging.getLogger(__name__)

# Константы для YooKassa
YOOKASSA_PROVIDER_TOKEN = settings.YOOKASSA_SECRET_KEY
SHOP_ID = settings.YOOKASSA_SHOP_ID


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показать содержимое корзины"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста.\n\n"
            "Загляните в каталог, чтобы найти что-нибудь интересное!",
            reply_markup=main_menu_kb()
        )
        return
    
    total_price = sum(item[3] * item[4] for item in cart_items)  # price * quantity
    cart_text = "🛒 Ваша корзина:\n\n"
    
    for item in cart_items:
        product_id, name, price, quantity = item[1], item[2], item[3], item[4]
        cart_text += f"📦 {name}\n"
        cart_text += f"💰 Цена: {price} ₽\n"
        cart_text += f"📊 Количество: {quantity}\n"
        cart_text += f"💵 Сумма: {price * quantity} ₽\n\n"
    
    cart_text += f"━━━━━━━━━━━━━\n"
    cart_text += f"💎 Итого: {total_price} ₽"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(cart_text, reply_markup=kb)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    await callback.message.answer(
        "🗑 Корзина очищена!",
        reply_markup=main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    """Оформление заказа и оплата через Telegram Payments"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.answer(
            "❌ Ваша корзина пуста!",
            reply_markup=main_menu_kb()
        )
        await callback.answer()
        return
    
    # Рассчитываем общую стоимость
    total_amount = sum(item[3] * item[4] for item in cart_items)
    
    # Создаем описание заказа
    order_description = "Покупка цифровых товаров:\n"
    for item in cart_items:
        product_id, name, price, quantity = item[1], item[2], item[3], item[4]
        order_description += f"• {name} x{quantity}\n"
    
    # Отправляем счет на оплату через Telegram Payments
    await callback.message.answer_invoice(
        title="🛍 Покупка в CyberMarket",
        description=order_description,
        payload=f"order_{user_id}_{int(asyncio.get_event_loop().time())}",
        provider_token=YOOKASSA_PROVIDER_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label="Товары", amount=int(total_amount * 100))  # в копейках
        ],
        start_parameter="cybermarket_payment"
    )
    
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение предварительной проверки платежа"""
    try:
        # Проверяем, что пользователь существует в базе
        user_id = pre_checkout_query.from_user.id
        user = await db.get_user(user_id)
        
        if not user:
            await pre_checkout_query.answer(
                ok=False,
                error_message="Пользователь не найден. Пожалуйста, начните с /start"
            )
            return
        
        # Проверяем, что корзина не пуста
        cart_items = await db.get_cart(user_id)
        if not cart_items:
            await pre_checkout_query.answer(
                ok=False,
                error_message="Ваша корзина пуста. Пожалуйста, добавьте товары"
            )
            return
        
        # Проверяем сумму платежа
        expected_amount = sum(item[3] * item[4] for item in cart_items) * 100
        if pre_checkout_query.total_amount != expected_amount:
            await pre_checkout_query.answer(
                ok=False,
                error_message="Сумма платежа не совпадает. Попробуйте еще раз"
            )
            return
        
        await pre_checkout_query.answer(ok=True)
        
    except Exception as e:
        logger.error(f"Error in pre_checkout_handler: {e}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Произошла ошибка при обработке платежа"
        )


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    """Обработка успешного платежа"""
    try:
        user_id = message.from_user.id
        payment_info = message.successful_payment
        
        # Получаем корзину пользователя
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            await message.answer(
                "❌ Ошибка: корзина пуста, но платеж прошел.\n"
                "Пожалуйста, обратитесь в поддержку.",
                reply_markup=main_menu_kb()
            )
            return
        
        # Создаем заказ в базе данных
        order_id = await db.create_order(
            user_id=user_id,
            total_amount=payment_info.total_amount / 100,
            payment_id=payment_info.telegram_payment_charge_id
        )
        
        # Добавляем товары в заказ
        for item in cart_items:
            product_id, name, price, quantity = item[1], item[2], item[3], item[4]
            await db.add_order_item(order_id, product_id, quantity, price)
        
        # Получаем все товары из корзины для выдачи
        purchased_items = []
        for item in cart_items:
            product_id = item[1]
            product = await db.get_product(product_id)
            if product:
                purchased_items.append(product)
        
        # Формируем сообщение с товарами
        success_text = (
            "✅ Оплата прошла успешно!\n\n"
            "🎉 Спасибо за покупку!\n\n"
            "📦 Ваши товары:\n\n"
        )
        
        for product in purchased_items:
            product_id, name, description, price, category, file_path, download_link, is_available = product
            
            success_text += f"━━━━━━━━━━━━━\n"
            success_text += f"📦 {name}\n"
            success_text += f"📝 {description}\n"
            success_text += f"💰 {price} ₽\n\n"
            
            if download_link:
                success_text += f"🔗 Ссылка для скачивания: {download_link}\n\n"
            elif file_path:
                success_text += f"📁 Файл: {file_path}\n\n"
        
        # Очищаем корзину после успешной покупки
        await db.clear_cart(user_id)
        
        # Отправляем сообщение с товарами
        await message.answer(
            success_text,
            reply_markup=main_menu_kb()
        )
        
        # Отправляем файлы, если они есть
        for product in purchased_items:
            product_id, name, description, price, category, file_path, download_link, is_available = product
            
            if file_path and not download_link:
                try:
                    with open(file_path, 'rb') as file:
                        await message.answer_document(
                            document=file,
                            caption=f"📦 {name}"
                        )
                except FileNotFoundError:
                    logger.error(f"File not found: {file_path}")
                    await message.answer(
                        f"⚠️ Файл для товара «{name}» не найден.\n"
                        f"Пожалуйста, обратитесь в поддержку."
                    )
                except Exception as e:
                    logger.error(f"Error sending file: {e}")
        
        # Отправляем чек
        await message.answer(
            f"🧾 Чек об оплате:\n"
            f"ID платежа: {payment_info.telegram_payment_charge_id}\n"
            f"Сумма: {payment_info.total_amount / 100} ₽\n"
            f"Валюта: {payment_info.currency}"
        )
        
    except Exception as e:
        logger.error(f"Error in successful_payment: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке платежа.\n"
            "Пожалуйста, обратитесь в поддержку.",
            reply_markup=main_menu_kb()
        )


@router.message(F.text == "💳 Оплатить")
async def pay_button(message: Message):
    """Обработка нажатия кнопки оплаты"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "❌ Ваша корзина пуста!",
            reply_markup=main_menu_kb()
        )
        return
    
    total_amount = sum(item[3] * item[4] for item in cart_items)
    
    order_description = "Покупка цифровых товаров:\n"
    for item in cart_items:
        product_id, name, price, quantity = item[1], item[2], item[3], item[4]
        order_description += f"• {name} x{quantity}\n"
    
    await message.answer_invoice(
        title="🛍 Покупка в CyberMarket",
        description=order_description,
        payload=f"order_{user_id}_{int(asyncio.get_event_loop().time())}",
        provider_token=YOOKASSA_PROVIDER_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label="Товары", amount=int(total_amount * 100))
        ],
        start_parameter="cybermarket_payment"
    )


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавление товара в корзину"""
    try:
        product_id = int(callback.data.replace("add_", ""))
        user_id = callback.from_user.id
        
        # Проверяем, что товар существует
        product = await db.get_product(product_id)
        if not product:
            await callback.message.answer(
                "❌ Товар не найден или был удален.",
                reply_markup=main_menu_kb()
            )
            await callback.answer()
            return
        
        # Добавляем товар в корзину
        await db.add_to_cart(user_id, product_id)
        
        await callback.message.answer(
            f"✅ Товар «{product[1]}» добавлен в корзину!\n\n"
            f"Продолжить покупки или перейти к оплате?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="view_cart")],
                [InlineKeyboardButton(text="⬅️ Продолжить покупки", callback_data="back_to_products")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при добавлении товара в корзину.",
            reply_markup=main_menu_kb()
        )
        await callback.answer()


@router.callback_query(F.data == "view_cart")
async def view_cart(callback: CallbackQuery):
    """Просмотр корзины"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.answer(
            "🛒 Ваша корзина пуста.",
            reply_markup=main_menu_kb()
        )
        await callback.answer()
        return
    
    total_price = sum(item[3] * item[4] for item in cart_items)
    cart_text = "🛒 Ваша корзина:\n\n"
    
    for item in cart_items:
        product_id, name, price, quantity = item[1], item[2], item[3], item[4]
        cart_text += f"📦 {name}\n"
        cart_text += f"💰 Цена: {price} ₽\n"
        cart_text += f"📊 Количество: {quantity}\n"
        cart_text += f"💵 Сумма: {price * quantity} ₽\n\n"
    
    cart_text += f"━━━━━━━━━━━━━\n"
    cart_text += f"💎 Итого: {total_price} ₽"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.answer(cart_text, reply_markup=kb)
    await callback.answer()


@router.message(F.text == "💳 Оплатить")
async def pay_command(message: Message):
    """Команда для оплаты"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "❌ Ваша корзина пуста!",
            reply_markup=main_menu_kb()
        )
        return
    
    total_amount = sum(item[3] * item[4] for item in cart_items)
    
    order_description = "Покупка цифровых товаров:\n"
    for item in cart_items:
        product_id, name, price, quantity = item[1], item[2], item[3], item[4]
        order_description += f"• {name} x{quantity}\n"
    
    await message.answer_invoice(
        title="🛍 Покупка в CyberMarket",
        description=order_description,
        payload=f"order_{user_id}_{int(asyncio.get_event_loop().time())}",
        provider_token=YOOKASSA_PROVIDER_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label="Товары", amount=int(total_amount * 100))
        ],
        start_parameter="cybermarket_payment"
    )
