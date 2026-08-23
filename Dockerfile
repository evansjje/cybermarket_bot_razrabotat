# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Union, List


class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    YOOKASSA_SHOP_ID: str = "YOUR_SHOP_ID"
    YOOKASSA_SECRET_KEY: str = "YOUR_SECRET_KEY"
    ADMIN_IDS: Union[List[int], str] = "123456789"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v


settings = Settings()

# database.py
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA foreign_keys = ON")
        await self._create_tables()
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def _create_tables(self) -> None:
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0.0,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                total_price REAL,
                status TEXT DEFAULT 'pending',
                payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS referral_system (
                referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                referred_user_id INTEGER,
                reward REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_user_id) REFERENCES users(user_id)
            );
        """)

    async def get_user(self, user_id: int) -> Optional[tuple]:
        cursor = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str) -> None:
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        await self.conn.commit()

    async def get_products_by_category(self, category: str) -> List[tuple]:
        cursor = await self.conn.execute("SELECT * FROM products WHERE category = ?", (category,))
        return await cursor.fetchall()

    async def get_product(self, product_id: int) -> Optional[tuple]:
        cursor = await self.conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        return await cursor.fetchone()

    async def add_product(self, name: str, description: str, price: float, category: str, file_path: str) -> None:
        await self.conn.execute(
            "INSERT INTO products (name, description, price, category, file_path) VALUES (?, ?, ?, ?, ?)",
            (name, description, price, category, file_path)
        )
        await self.conn.commit()

    async def update_product(self, product_id: int, name: str, description: str, price: float, category: str, file_path: str) -> None:
        await self.conn.execute(
            "UPDATE products SET name = ?, description = ?, price = ?, category = ?, file_path = ? WHERE product_id = ?",
            (name, description, price, category, file_path, product_id)
        )
        await self.conn.commit()

    async def delete_product(self, product_id: int) -> None:
        await self.conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        await self.conn.commit()

    async def add_order(self, user_id: int, product_id: int, quantity: int, total_price: float) -> int:
        cursor = await self.conn.execute(
            "INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES (?, ?, ?, ?)",
            (user_id, product_id, quantity, total_price)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_order(self, order_id: int) -> Optional[tuple]:
        cursor = await self.conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        return await cursor.fetchone()

    async def update_order_payment_id(self, order_id: int, payment_id: str) -> None:
        await self.conn.execute("UPDATE orders SET payment_id = ? WHERE order_id = ?", (payment_id, order_id))
        await self.conn.commit()

    async def update_order_status(self, order_id: int, status: str) -> None:
        await self.conn.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        await self.conn.commit()

    async def get_all_products(self) -> List[tuple]:
        cursor = await self.conn.execute("SELECT * FROM products")
        return await cursor.fetchall()

# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="👥 Реферальная программа")],
        [KeyboardButton(text="⭐️ Отзывы"), KeyboardButton(text="📞 Поддержка")],
        [KeyboardButton(text="🔐 Админ-панель")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def catalog_kb(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat, callback_data=f"cat_{cat}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def products_kb(products: list, category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=product[1], callback_data=f"prod_{product[0]}")
    builder.button(text="⬅️ Назад", callback_data=f"back_{category}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Добавить в корзину", callback_data=f"add_{product_id}")
    builder.button(text="⬅️ Назад", callback_data="back_catalog")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data=f"pay_{order_id}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def success_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    return builder.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Управление товарами", callback_data="admin_products")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=f"{product[1]} | {product[3]}₽", callback_data=f"admin_prod_{product[0]}")
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="⬅️ Назад", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"admin_edit_{product_id}")
    builder.button(text="🗑 Удалить", callback_data=f"admin_delete_{product_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_products")
    builder.adjust(1)
    return builder.as_markup()


def admin_categories_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in ["Скрипты", "Софт", "Мануалы"]:
        builder.button(text=cat, callback_data=f"admin_cat_{cat}")
    builder.button(text="⬅️ Назад", callback_data="admin_products")
    builder.adjust(1)
    return builder.as_markup()

# handlers/catalog.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import catalog_kb, products_kb, product_detail_kb, main_menu_kb

router = Router()
db = Database()


class CartStates(StatesGroup):
    waiting_for_quantity = State()


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    categories = ["Скрипты", "Софт", "Мануалы"]
    await message.answer("Выберите категорию:", reply_markup=catalog_kb(categories))


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split("_", 1)[1]
    products = await db.get_products_by_category(category)
    if products:
        await callback.message.edit_text(f"Товары в категории '{category}':", reply_markup=products_kb(products, category))
    else:
        await callback.message.edit_text("В этой категории пока нет товаров.", reply_markup=catalog_kb(["Скрипты", "Софт", "Мануалы"]))
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    if product:
        text = f"📦 {product[1]}\n\n{product[2]}\n\n💰 Цена: {product[3]} руб."
        await callback.message.edit_text(text, reply_markup=product_detail_kb(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    product = await db.get_product(product_id)
    if product:
        await db.add_order(user_id, product_id, 1, product[3])
        await callback.answer("✅ Товар добавлен в корзину!")
    await callback.answer()


@router.callback_query(F.data == "back_catalog")
async def back_to_catalog(callback: CallbackQuery):
    categories = ["Скрипты", "Софт", "Мануалы"]
    await callback.message.edit_text("Выберите категорию:", reply_markup=catalog_kb(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("back_"))
async def back_to_products(callback: CallbackQuery):
    category = callback.data.split("_", 1)[1]
    products = await db.get_products_by_category(category)
    if products:
        await callback.message.edit_text(f"Товары в категории '{category}':", reply_markup=products_kb(products, category))
    await callback.answer()

# handlers/payment.py
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
    if order[1] != user_id:
        await callback.answer("Это не ваш заказ")
        return

    payment = Payment.create({
        "amount": {
            "value": f"{order[4]:.2f}",
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
        f"💳 Оплата заказа #{order_id}\n\nСумма: {order[4]} руб.\n\n"
        f"Ссылка для оплаты: {payment.confirmation.confirmation_url}",
        reply_markup=payment_kb(order_id)
    )
    await callback.answer()


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
        product = await db.get_product(order[2])
        if product and product[5]:
            await message.answer_document(document=product[5], caption=f"✅ Спасибо за покупку!\n\n{product[1]}")
        else:
            await message.answer("✅ Оплата прошла успешно!", reply_markup=success_kb())

# handlers/admin.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import main_menu_kb, admin_menu_kb, admin_products_kb, admin_product_actions_kb, admin_categories_kb
from config import settings

router = Router()
db = Database()


class AdminStates(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()
    waiting_for_product_file = State()
    waiting_for_edit_product_name = State()
    waiting_for_edit_product_description = State()
    waiting_for_edit_product_price = State()
    waiting_for_edit_product_category = State()
    waiting_for_edit_product_file = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(F.text == "🔐 Админ-панель")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Доступ запрещен")
        return
    await message.answer("🔐 Админ-панель", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    await callback.message.edit_text("🔐 Админ-панель", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    products = await db.get_all_products()
    await callback.message.edit_text("📦 Управление товарами:", reply_markup=admin_products_kb(products))
    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    await state.set_state(AdminStates.waiting_for_product_name)
    await callback.message.edit_text("Введите название товара:")
    await callback.answer()


@router.message(AdminStates.waiting_for_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminStates.waiting_for_product_description)
    await message.answer("Введите описание товара:")


@router.message(AdminStates.waiting_for_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminStates.waiting_for_product_price)
    await message.answer("Введите цену товара:")


@router.message(AdminStates.waiting_for_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AdminStates.waiting_for_product_category)
        await message.answer("Выберите категорию:", reply_markup=admin_categories_kb())
    except ValueError:
        await message.answer("❌ Введите корректную цену")


@router.callback_query(F.data.startswith("admin_cat_"))
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    category = callback.data.split("_", 2)[2]
    await state.update_data(category=category)
    await state.set_state(AdminStates.waiting_for_product_file)
    await callback.message.edit_text("Отправьте файл товара:")
    await callback.answer()


@router.message(AdminStates.waiting_for_product_file)
async def admin_add_product_file(message: Message, state: FSMContext):
    if message.document:
        file_id = message.document.file_id
        data = await state.get_data()
        await db.add_product(data["name"], data["description"], data["price"], data["category"], file_id)
        await state.clear()
        await message.answer("✅ Товар добавлен!", reply_markup=admin_menu_kb())
    else:
        await message.answer("❌ Отправьте файл")


@router.callback_query(F.data.startswith("admin_prod_"))
async def admin_product_actions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[2])
    product = await db.get_product(product_id)
    if product:
        text = f"📦 {product[1]}\n\n{product[2]}\n\n💰 Цена: {product[3]} руб.\n📁 Категория: {product[4]}"
        await callback.message.edit_text(text, reply_markup=admin_product_actions_kb(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[2])
    await db.delete_product(product_id)
    products = await db.get_all_products()
    await callback.message.edit_text("📦 Управление товарами:", reply_markup=admin_products_kb(products))
    await callback.answer("✅ Товар удален")


@router.callback_query(F.data.startswith("admin_edit_"))
async def admin_edit_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_for_edit_product_name)
    await callback.message.edit_text("Введите новое название товара:")
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_product_name)
async def admin_edit_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminStates.waiting_for_edit_product_description)
    await message.answer("Введите новое описание товара:")


@router.message(AdminStates.waiting_for_edit_product_description)
async def admin_edit_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminStates.waiting_for_edit_product_price)
    await message.answer("Введите новую цену товара:")


@router.message(AdminStates.waiting_for_edit_product_price)
async def admin_edit_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AdminStates.waiting_for_edit_product_category)
        await message.answer("Выберите новую категорию:", reply_markup=admin_categories_kb())
    except ValueError:
        await message.answer("❌ Введите корректную цену")


@router.callback_query(F.data.startswith("admin_cat_"))
async def admin_edit_product_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    category = callback.data.split("_", 2)[2]
    await state.update_data(category=category)
    await state.set_state(AdminStates.waiting_for_edit_product_file)
    await callback.message.edit_text("Отправьте новый файл товара (или отправьте '-' для пропуска):")
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_product_file)
async def admin_edit_product_file(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.text == "-":
        product = await db.get_product(data["product_id"])
        if product:
            file_id = product[5]
    if file_id:
        await db.update_product(data["product_id"], data["name"], data["description"], data["price"], data["category"], file_id)
        await state.clear()
        await message.answer("✅ Товар обновлен!", reply_markup=admin_menu_kb())
    else:
        await message.answer("❌ Отправьте файл или '-'")

# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database import Database
from handlers import catalog, payment, admin
from keyboards import main_menu_kb

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot, db: Database):
    await db.connect()
    await bot.set_my_commands([
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/catalog", description="Открыть каталог"),
        BotCommand(command="/cart", description="Открыть корзину"),
        BotCommand(command="/help", description="Помощь"),
    ])


async def on_shutdown(bot: Bot, db: Database):
    await db.close()


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    db = Database()
    dp["db"] = db

    catalog.db = db
    payment.db = db
    admin.db = db

    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    @dp.message(commands=["start"])
    async def cmd_start(message):
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""

        await db.add_user(user_id, username, first_name, last_name)
        await message.answer(
            f"👋 Добро пожаловать, {first_name}!\n\n"
            "🛍 Здесь вы можете приобрести цифровые товары.\n"
            "Выберите действие в меню:",
            reply_markup=main_menu_kb()
        )

    @dp.message(commands=["catalog"])
    async def cmd_catalog(message):
        categories = ["Скрипты", "Софт", "Мануалы"]
        await message.answer("Выберите категорию:", reply_markup=catalog_kb(categories))

    @dp.message(commands=["cart"])
    async def cmd_cart(message):
        await message.answer("🛒 Ваша корзина пуста", reply_markup=main_menu_kb())

    @dp.message(commands=["help"])
    async def cmd_help(message):
        await message.answer(
            "📚 Помощь:\n\n"
            "🛍 Каталог - просмотр товаров\n"
            "🛒 Корзина - ваши покупки\n"
            "👥 Реферальная программа - приглашайте друзей\n"
            "⭐️ Отзывы - отзывы покупателей\n"
            "📞 Поддержка - связь с поддержкой",
            reply_markup=main_menu_kb()
        )

    @dp.callback_query(lambda c: c.data == "main_menu")
    async def main_menu_callback(callback):
        await callback.message.answer("Главное меню:", reply_markup=main_menu_kb())
        await callback.answer()

    @dp.message(F.text == "🛒 Корзина")
    async def show_cart(message: Message):
        await message.answer("🛒 Ваша корзина пуста", reply_markup=main_menu_kb())

    @dp.message(F.text == "👥 Реферальная программа")
    async def referral_program(message: Message):
        await message.answer(
            "👥 Реферальная программа\n\n"
            "Приглашайте друзей и получайте бонусы!\n"
            "Ваша реферальная ссылка: https://t.me/your_bot?start=ref_" + str(message.from_user.id),
            reply_markup=main_menu_kb()
        )

    @dp.message(F.text == "⭐️ Отзывы")
    async def reviews(message: Message):
        await message.answer("⭐️ Отзывы наших покупателей:\n\n🌟 Отличный магазин!", reply_markup=main_menu_kb())

    @dp.message(F.text == "📞 Поддержка")
    async def support(message: Message):
        await message.answer("📞 Свяжитесь с поддержкой: @support", reply_markup=main_menu_kb())

    await on_startup(bot, db)
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot, db)


if __name__ == "__main__":
    asyncio.run(main())

# requirements.txt
aiogram>=3.4.0
aiosqlite>=0.19.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
yookassa>=3.0.0

# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
