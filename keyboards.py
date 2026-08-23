from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional, Dict, Any
from config import Settings

settings = Settings()

# ==================== ГЛАВНОЕ МЕНЮ ====================

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    buttons = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="👥 Реферальная программа")],
        [KeyboardButton(text="⭐️ Отзывы")],
        [KeyboardButton(text="📞 Поддержка")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

# ==================== КАТАЛОГ ====================

def get_catalog_menu(categories: List[str]) -> InlineKeyboardMarkup:
    """Меню каталога с категориями."""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=f"📁 {category}",
            callback_data=f"category:{category}"
        )
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_products_menu(products: List[Dict[str, Any]], category: str) -> InlineKeyboardMarkup:
    """Меню товаров в категории."""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"📦 {product['name']} - {product['price']}₽",
            callback_data=f"product:{product['id']}"
        )
    builder.button(text="⬅️ Назад", callback_data="back_to_categories")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_product_actions(product_id: int) -> InlineKeyboardMarkup:
    """Действия с товаром."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Добавить в корзину", callback_data=f"add_to_cart:{product_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_products")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# ==================== КОРЗИНА ====================

def get_cart_menu(cart_items: List[Dict[str, Any]], total_price: float) -> InlineKeyboardMarkup:
    """Меню корзины."""
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        builder.button(
            text=f"❌ {item['name']} - {item['price']}₽",
            callback_data=f"remove_from_cart:{item['product_id']}"
        )
    builder.button(text="💳 Оплатить", callback_data="checkout")
    builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# ==================== РЕФЕРАЛЬНАЯ ПРОГРАММА ====================

def get_referral_menu() -> InlineKeyboardMarkup:
    """Меню реферальной программы."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Получить реферальную ссылку", callback_data="get_referral_link")
    builder.button(text="📊 Моя статистика", callback_data="referral_stats")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# ==================== ОТЗЫВЫ ====================

def get_reviews_menu() -> InlineKeyboardMarkup:
    """Меню отзывов."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Оставить отзыв", callback_data="write_review")
    builder.button(text="📖 Читать отзывы", callback_data="read_reviews")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# ==================== ПОДДЕРЖКА ====================

def get_support_menu() -> InlineKeyboardMarkup:
    """Меню поддержки."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📞 Связаться с поддержкой",
        url=f"https://t.me/{settings.SUPPORT_USERNAME}"
    )
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# ==================== ОПЛАТА ====================

def get_payment_menu(order_id: int) -> InlineKeyboardMarkup:
    """Меню оплаты."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить через YooKassa", callback_data=f"pay_yookassa:{order_id}")
    if settings.TELEGRAM_PAYMENT_TOKEN:
        builder.button(text="💳 Оплатить через Telegram", callback_data=f"pay_telegram:{order_id}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# ==================== АДМИН-ПАНЕЛЬ ====================

def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="📝 Редактировать товар", callback_data="admin_edit_product")
    builder.button(text="🗑 Удалить товар", callback_data="admin_delete_product")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📦 Управление категориями", callback_data="admin_categories")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_product_actions(product_id: int) -> InlineKeyboardMarkup:
    """Действия с товаром в админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить название", callback_data=f"admin_edit_name:{product_id}")
    builder.button(text="💰 Изменить цену", callback_data=f"admin_edit_price:{product_id}")
    builder.button(text="📝 Изменить описание", callback_data=f"admin_edit_desc:{product_id}")
    builder.button(text="📁 Изменить категорию", callback_data=f"admin_edit_cat:{product_id}")
    builder.button(text="🔗 Изменить ссылку", callback_data=f"admin_edit_link:{product_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_categories_menu(categories: List[str]) -> InlineKeyboardMarkup:
    """Меню управления категориями."""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=f"🗑 {category}",
            callback_data=f"admin_del_cat:{category}"
        )
    builder.button(text="➕ Добавить категорию", callback_data="admin_add_cat")
    builder.button(text="⬅️ Назад", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_confirm_delete(product_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления товара."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"admin_confirm_del:{product_id}")
    builder.button(text="❌ Отмена", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_confirm_del_cat(category: str) -> InlineKeyboardMarkup:
    """Подтверждение удаления категории."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"admin_confirm_del_cat:{category}")
    builder.button(text="❌ Отмена", callback_data="admin_categories")
    builder.adjust(1)
    return builder.as_markup()

# ==================== ОБЩИЕ ====================

def get_back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Кнопка назад."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_payment(order_id: int) -> InlineKeyboardMarkup:
    """Подтверждение оплаты."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я оплатил", callback_data=f"confirm_payment:{order_id}")
    builder.button(text="❌ Отмена", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
