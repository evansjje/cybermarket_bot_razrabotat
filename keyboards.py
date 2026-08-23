from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Optional, List, Dict, Any

# ==================== ГЛАВНОЕ МЕНЮ ====================

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛍 Каталог"),
        KeyboardButton(text="🛒 Корзина")
    )
    builder.row(
        KeyboardButton(text="👥 Реферальная программа"),
        KeyboardButton(text="⭐️ Отзывы")
    )
    builder.row(
        KeyboardButton(text="📞 Поддержка")
    )
    return builder.as_markup(resize_keyboard=True)

# ==================== КАТАЛОГ ====================

def get_catalog_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=f"📂 {category}",
            callback_data=f"category:{category}"
        )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура с товарами в категории"""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['name']} - {product['price']}₽",
            callback_data=f"product:{product['id']}"
        )
    builder.button(
        text="🔙 Назад к категориям",
        callback_data="back_to_categories"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_product_keyboard(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для конкретного товара"""
    builder = InlineKeyboardBuilder()
    if not in_cart:
        builder.button(
            text="🛒 Добавить в корзину",
            callback_data=f"add_to_cart:{product_id}"
        )
    else:
        builder.button(
            text="✅ В корзине",
            callback_data="already_in_cart"
        )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_products"
    )
    builder.adjust(1)
    return builder.as_markup()

# ==================== КОРЗИНА ====================

def get_cart_keyboard(cart_items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        builder.button(
            text=f"❌ {item['name']}",
            callback_data=f"remove_from_cart:{item['id']}"
        )
    builder.button(
        text="💳 Оплатить",
        callback_data="checkout"
    )
    builder.button(
        text="🗑 Очистить корзину",
        callback_data="clear_cart"
    )
    builder.button(
        text="🔙 В каталог",
        callback_data="back_to_categories"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 Оплатить через YooKassa",
        url=payment_url
    )
    builder.button(
        text="✅ Я оплатил",
        callback_data="check_payment"
    )
    builder.button(
        text="🔙 Отменить",
        callback_data="cancel_payment"
    )
    builder.adjust(1)
    return builder.as_markup()

# ==================== РЕФЕРАЛЬНАЯ ПРОГРАММА ====================

def get_referral_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔗 Моя реферальная ссылка",
        callback_data="my_referral_link"
    )
    builder.button(
        text="💰 Мои рефералы",
        callback_data="my_referrals"
    )
    builder.button(
        text="💵 Вывести средства",
        callback_data="withdraw"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()

# ==================== ОТЗЫВЫ ====================

def get_reviews_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отзывов"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📝 Оставить отзыв",
        callback_data="write_review"
    )
    builder.button(
        text="📖 Читать отзывы",
        callback_data="read_reviews"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()

# ==================== ПОДДЕРЖКА ====================

def get_support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поддержки"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📨 Написать в поддержку",
        callback_data="contact_support"
    )
    builder.button(
        text="❓ FAQ",
        callback_data="faq"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()

# ==================== АДМИН-ПАНЕЛЬ ====================

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Добавить товар",
        callback_data="admin_add_product"
    )
    builder.button(
        text="📝 Редактировать товар",
        callback_data="admin_edit_product"
    )
    builder.button(
        text="🗑 Удалить товар",
        callback_data="admin_delete_product"
    )
    builder.button(
        text="📊 Статистика",
        callback_data="admin_stats"
    )
    builder.button(
        text="👥 Пользователи",
        callback_data="admin_users"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_admin_products_keyboard(products: List[Dict[str, Any]], action: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора товара для админа"""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['name']} - {product['price']}₽",
            callback_data=f"admin_{action}:{product['id']}"
        )
    builder.button(
        text="🔙 Назад",
        callback_data="admin_back"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_admin_edit_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура редактирования товара"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✏️ Название",
        callback_data=f"edit_name:{product_id}"
    )
    builder.button(
        text="📝 Описание",
        callback_data=f"edit_description:{product_id}"
    )
    builder.button(
        text="💰 Цена",
        callback_data=f"edit_price:{product_id}"
    )
    builder.button(
        text="📂 Категория",
        callback_data=f"edit_category:{product_id}"
    )
    builder.button(
        text="📎 Файл",
        callback_data=f"edit_file:{product_id}"
    )
    builder.button(
        text="🔗 Ссылка",
        callback_data=f"edit_link:{product_id}"
    )
    builder.button(
        text="✅ Готово",
        callback_data="admin_back"
    )
    builder.adjust(2)
    return builder.as_markup()

def get_admin_confirm_keyboard(action: str, product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=f"confirm_{action}:{product_id}"
    )
    builder.button(
        text="❌ Отмена",
        callback_data="admin_back"
    )
    builder.adjust(2)
    return builder.as_markup()

# ==================== ОБЩИЕ КЛАВИАТУРЫ ====================

def get_back_keyboard(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Универсальная клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔙 Назад",
        callback_data=callback_data
    )
    return builder.as_markup()

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да",
        callback_data=f"confirm_{action}"
    )
    builder.button(
        text="❌ Нет",
        callback_data="cancel"
    )
    builder.adjust(2)
    return builder.as_markup()

def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 YooKassa",
        callback_data="pay_yookassa"
    )
    builder.button(
        text="⚡️ Telegram Payments",
        callback_data="pay_telegram"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_cart"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_delivery_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура способа доставки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📎 Файл",
        callback_data="delivery_file"
    )
    builder.button(
        text="🔗 Ссылка",
        callback_data="delivery_link"
    )
    builder.adjust(2)
    return builder.as_markup()
