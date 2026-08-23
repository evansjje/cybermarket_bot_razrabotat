import asyncio
import logging
import sys
from typing import Union

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    PreCheckoutQuery, LabeledPrice, ContentType
)
from aiogram.exceptions import TelegramBadRequest

# Импорты из других модулей проекта
from config import settings
from database import Database
from keyboards import (
    main_menu_keyboard, catalog_keyboard, cart_keyboard,
    admin_menu_keyboard, product_management_keyboard,
    confirm_payment_keyboard, referral_keyboard
)
from handlers.catalog import router as catalog_router
from handlers.payment import router as payment_router
from handlers.admin import router as admin_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация роутеров
main_router = Router()

# ==================== ОБРАБОТЧИКИ ОСНОВНОГО МЕНЮ ====================

@main_router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    # Регистрация пользователя в базе данных
    await db.add_user(user_id, username)
    
    # Проверка на реферальный код
    args = message.text.split()
    if len(args) > 1:
        referral_code = args[1]
        await db.process_referral(user_id, referral_code)
    
    await message.answer(
        f"👋 Добро пожаловать в CyberMarket_Bot!\n\n"
        f"🛒 Магазин цифровых товаров: скрипты, софт, мануалы.\n\n"
        f"Выберите действие в меню:",
        reply_markup=main_menu_keyboard()
    )

@main_router.message(F.text == "📦 Каталог")
async def show_catalog(message: Message, db: Database):
    """Показать каталог товаров"""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("📭 Каталог пуст. Загляните позже!")
        return
    
    # Создаем клавиатуру с категориями
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📁 {cat[1]}", callback_data=f"cat_{cat[0]}")]
        for cat in categories
    ])
    
    await message.answer("📦 Выберите категорию:", reply_markup=kb)

@main_router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, db: Database):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return
    
    total_price = 0
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    for item in cart_items:
        product_id, name, price, quantity = item
        cart_text += f"▫️ {name} — {price} ₽ x {quantity}\n"
        total_price += price * quantity
    
    cart_text += f"\n💰 <b>Итого: {total_price} ₽</b>"
    
    await message.answer(
        cart_text,
        reply_markup=cart_keyboard(total_price)
    )

@main_router.message(F.text == "👥 Реферальная программа")
async def show_referral(message: Message, db: Database):
    """Показать реферальную программу"""
    user_id = message.from_user.id
    referral_info = await db.get_referral_info(user_id)
    
    if referral_info:
        referral_code, referral_count, referral_balance = referral_info
        referral_link = f"https://t.me/{settings.BOT_USERNAME}?start={referral_code}"
        
        text = (
            f"👥 <b>Реферальная программа</b>\n\n"
            f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
            f"📊 Приглашено друзей: {referral_count}\n"
            f"💰 Заработано: {referral_balance} ₽\n\n"
            f"Приглашайте друзей и получайте 10% от их покупок!"
        )
    else:
        text = "👥 Реферальная программа\n\nПриглашайте друзей и получайте бонусы!"
    
    await message.answer(text, reply_markup=referral_keyboard())

@main_router.message(F.text == "⭐️ Отзывы")
async def show_reviews(message: Message):
    """Показать отзывы"""
    await message.answer(
        "⭐️ <b>Отзывы наших клиентов:</b>\n\n"
        "✅ «Отличный бот, всё работает!» — Иван\n"
        "✅ «Быстрая доставка товара, рекомендую!» — Мария\n"
        "✅ «Качественные скрипты, спасибо!» — Дмитрий\n\n"
        "Хотите оставить отзыв? Напишите @support"
    )

@main_router.message(F.text == "🆘 Поддержка")
async def show_support(message: Message):
    """Показать контакты поддержки"""
    await message.answer(
        "🆘 <b>Поддержка</b>\n\n"
        "📧 Email: support@cybermarket.com\n"
        "💬 Telegram: @cybermarket_support\n"
        "🕐 Время работы: 24/7\n\n"
        "Опишите вашу проблему, и мы поможем!"
    )

@main_router.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: Message, db: Database):
    """Показать админ-панель"""
    user_id = message.from_user.id
    
    if user_id != settings.ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа к админ-панели!")
        return
    
    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Управление товарами и заказами:",
        reply_markup=admin_menu_keyboard()
    )

# ==================== ОБРАБОТЧИКИ КАТЕГОРИЙ И ТОВАРОВ ====================

@main_router.callback_query(F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, db: Database):
    """Обработчик выбора категории"""
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products_by_category(category_id)
    
    if not products:
        await callback.message.answer("📭 В этой категории пока нет товаров.")
        await callback.answer()
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🛒 {prod[1]} — {prod[3]} ₽",
            callback_data=f"prod_{prod[0]}"
        )]
        for prod in products
    ])
    
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_catalog")
    ])
    
    await callback.message.edit_text(
        f"📦 <b>Товары в категории:</b>",
        reply_markup=kb
    )
    await callback.answer()

@main_router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, db: Database):
    """Возврат к каталогу"""
    categories = await db.get_categories()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📁 {cat[1]}", callback_data=f"cat_{cat[0]}")]
        for cat in categories
    ])
    
    await callback.message.edit_text(
        "📦 Выберите категорию:",
        reply_markup=kb
    )
    await callback.answer()

@main_router.callback_query(F.data.startswith("prod_"))
async def process_product(callback: CallbackQuery, db: Database):
    """Обработчик выбора товара"""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.message.answer("❌ Товар не найден.")
        await callback.answer()
        return
    
    product_id, name, description, price, category_id, file_path = product
    
    text = (
        f"📦 <b>{name}</b>\n\n"
        f"📝 {description}\n\n"
        f"💰 Цена: {price} ₽"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛒 Добавить в корзину",
                callback_data=f"add_{product_id}"
            ),
            InlineKeyboardButton(
                text="💳 Купить сейчас",
                callback_data=f"buy_{product_id}"
            )
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_catalog")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@main_router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавление товара в корзину"""
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    await db.add_to_cart(user_id, product_id)
    
    await callback.answer("✅ Товар добавлен в корзину!")
    
    # Показываем обновленную корзину
    cart_items = await db.get_cart(user_id)
    total_price = sum(item[2] * item[3] for item in cart_items)
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        product_id, name, price, quantity = item
        cart_text += f"▫️ {name} — {price} ₽ x {quantity}\n"
    cart_text += f"\n💰 <b>Итого: {total_price} ₽</b>"
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=cart_keyboard(total_price)
    )

# ==================== ОБРАБОТЧИКИ ОПЛАТЫ ====================

@main_router.callback_query(F.data.startswith("buy_"))
async def process_payment(callback: CallbackQuery, db: Database):
    """Обработчик покупки товара"""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.message.answer("❌ Товар не найден.")
        await callback.answer()
        return
    
    product_id, name, description, price, category_id, file_path = product
    
    # Проверяем, настроена ли оплата
    if not settings.PAYMENT_TOKEN or settings.PAYMENT_TOKEN == "YOUR_PAYMENT_TOKEN":
        await callback.message.answer(
            "⚠️ Оплата временно недоступна.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой."
        )
        await callback.answer()
        return
    
    # Создаем счет на оплату через Telegram Payments
    await callback.message.answer_invoice(
        title=name,
        description=description[:255] if len(description) > 255 else description,
        payload=f"product_{product_id}",
        provider_token=settings.PAYMENT_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=name, amount=price * 100)],  # в копейках
        start_parameter="cybermarket_payment"
    )
    await callback.answer()

@main_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery, db: Database):
    """Обработка предварительной проверки оплаты"""
    # Проверяем, что товар существует
    payload = pre_checkout.invoice_payload
    if payload.startswith("product_"):
        product_id = int(payload.split("_")[1])
        product = await db.get_product(product_id)
        if not product:
            await pre_checkout.answer(False, error_message="Товар не найден")
            return
    
    await pre_checkout.answer(True)

@main_router.message(F.successful_payment)
async def process_successful_payment(message: Message, db: Database):
    """Обработка успешной оплаты"""
    payment = message.successful_payment
    payload = payment.invoice_payload
    
    if payload.startswith("product_"):
        product_id = int(payload.split("_")[1])
        product = await db.get_product(product_id)
        
        if product:
            product_id, name, description, price, category_id, file_path = product
            
            # Записываем заказ в базу данных
            await db.create_order(
                user_id=message.from_user.id,
                product_id=product_id,
                amount=payment.total_amount / 100
            )
            
            # Отправляем товар пользователю
            if file_path:
                try:
                    # Отправляем файл, если он существует
                    with open(file_path, 'rb') as f:
                        await message.answer_document(
                            document=f,
                            caption=f"✅ Оплата получена!\n\n📦 Ваш товар: {name}\n\nСпасибо за покупку!"
                        )
                except FileNotFoundError:
                    # Если файл не найден, отправляем ссылку
                    await message.answer(
                        f"✅ Оплата получена!\n\n"
                        f"📦 Ваш товар: {name}\n"
                        f"🔗 Ссылка на скачивание: {file_path}\n\n"
                        f"Спасибо за покупку!"
                    )
            else:
                await message.answer(
                    f"✅ Оплата получена!\n\n"
                    f"📦 Ваш товар: {name}\n\n"
                    f"Спасибо за покупку!"
                )
            
            # Начисляем реферальный бонус
            await db.add_referral_bonus(message.from_user.id, payment.total_amount / 100)

# ==================== ОБРАБОТЧИКИ КОРЗИНЫ ====================

@main_router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, db: Database):
    """Оформление заказа из корзины"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.answer("🛒 Корзина пуста!")
        return
    
    total_price = sum(item[2] * item[3] for item in cart_items)
    
    # Проверяем, настроена ли оплата
    if not settings.PAYMENT_TOKEN or settings.PAYMENT_TOKEN == "YOUR_PAYMENT_TOKEN":
        await callback.message.answer(
            "⚠️ Оплата временно недоступна.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой."
        )
        await callback.answer()
        return
    
    # Создаем счет на оплату всей корзины
    prices = [
        LabeledPrice(label=item[1], amount=item[2] * 100 * item[3])
        for item in cart_items
    ]
    
    await callback.message.answer_invoice(
        title="Покупка в CyberMarket",
        description=f"Покупка {len(cart_items)} товаров на сумму {total_price} ₽",
        payload="cart_checkout",
        provider_token=settings.PAYMENT_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="cybermarket_cart"
    )
    await callback.answer()

@main_router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистка корзины"""
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    
    await callback.message.edit_text(
        "🗑 Корзина очищена!",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

# ==================== ОБРАБОТЧИКИ РЕФЕРАЛЬНОЙ ПРОГРАММЫ ====================

@main_router.callback_query(F.data == "referral_withdraw")
async def referral_withdraw(callback: CallbackQuery, db: Database):
    """Вывод реферальных средств"""
    user_id = callback.from_user.id
    referral_info = await db.get_referral_info(user_id)
    
    if not referral_info:
        await callback.answer("❌ У вас нет реферального баланса!")
        return
    
    referral_code, referral_count, referral_balance = referral_info
    
    if referral_balance < 100:
        await callback.answer(
            f"Минимальная сумма для вывода: 100 ₽\n"
            f"Ваш баланс: {referral_balance} ₽",
            show_alert=True
        )
        return
    
    # Здесь можно добавить логику вывода средств
    await callback.message.answer(
        f"💰 Запрос на вывод средств!\n\n"
        f"Сумма: {referral_balance} ₽\n"
        f"Средства будут переведены в течение 24 часов.\n\n"
        f"Для уточнения деталей напишите @cybermarket_support"
    )
    await callback.answer()

# ==================== ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ ====================

@main_router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery, db: Database):
    """Управление товарами"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Нет доступа!")
        return
    
    products = await db.get_all_products()
    
    if not products:
        await callback.message.edit_text(
            "📭 Товаров пока нет.\n"
            "Добавьте первый товар!",
            reply_markup=product_management_keyboard()
        )
        await callback.answer()
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✏️ {prod[1]} — {prod[3]} ₽",
            callback_data=f"admin_edit_{prod[0]}"
        )]
        for prod in products
    ])
    
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")
    ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
    ])
    
    await callback.message.edit_text(
        "⚙️ <b>Управление товарами:</b>",
        reply_markup=kb
    )
    await callback.answer()

@main_router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery, db: Database):
    """Просмотр заказов"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Нет доступа!")
        return
    
    orders = await db.get_all_orders()
    
    if not orders:
        await callback.message.edit_text(
            "📭 Заказов пока нет.",
            reply_markup=admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    orders_text = "📋 <b>Последние заказы:</b>\n\n"
    for order in orders[:10]:  # Показываем последние 10 заказов
        order_id, user_id, product_id, amount, date = order
        orders_text += f"#{order_id} | Пользователь: {user_id} | Сумма: {amount} ₽ | {date}\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(orders_text, reply_markup=kb)
    await callback.answer()

@main_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Возврат в админ-меню"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Нет доступа!")
        return
    
    await callback.message.edit_text(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Управление товарами и заказами:",
        reply_markup=admin_menu_keyboard()
    )
    await callback.answer()

# ==================== ОБРАБОТЧИКИ ОТЗЫВОВ ====================

@main_router.callback_query(F.data == "leave_review")
async def leave_review(callback: CallbackQuery):
    """Оставить отзыв"""
    await callback.message.answer(
        "⭐️ <b>Оставьте отзыв</b>\n\n"
        "Напишите ваш отзыв в чат, и он будет опубликован после модерации.\n\n"
        "Формат: <code>Отзыв: ваш текст</code>"
    )
    await callback.answer()

@main_router.message(F.text.startswith("Отзыв:"))
async def process_review(message: Message):
    """Обработка отзыва"""
    review_text = message.text.replace("Отзыв:", "").strip()
    
    if not review_text:
        await message.answer("❌ Пожалуйста, напишите текст отзыва.")
        return
    
    # Здесь можно сохранить отзыв в базу данных
    await message.answer(
        "✅ Спасибо за ваш отзыв!\n"
        "Он будет опубликован после модерации."
    )

# ==================== ОБРАБОТЧИКИ ПОДДЕРЖКИ ====================

@main_router.message(F.text == "📞 Связаться с поддержкой")
async def contact_support(message: Message):
    """Связаться с поддержкой"""
    await message.answer(
        "📞 <b>Связаться с поддержкой</b>\n\n"
        "Напишите нам в Telegram: @cybermarket_support\n"
        "Или оставьте сообщение здесь, и мы ответим в ближайшее время."
    )

# ==================== ОБРАБОТЧИКИ ДЛЯ НЕИЗВЕСТНЫХ КОМАНД ====================

@main_router.message()
async def unknown_command(message: Message):
    """Обработчик неизвестных команд"""
    await message.answer(
        "❌ Неизвестная команда.\n"
        "Используйте /start для начала работы с ботом."
    )

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

async def main():
    """Главная функция запуска бота"""
    # Инициализация базы данных
    db = Database(settings.DATABASE_PATH)
    await db.init()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(main_router)
    dp.include_router(catalog_router)
    dp.include_router(payment_router)
    dp.include_router(admin_router)
    
    # Передаем db в контекст
    dp.workflow_data['db'] = db
    
    # Запуск бота
    logger.info("Бот запущен!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)
