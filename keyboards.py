from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

# ==================== ГЛАВНОЕ МЕНЮ ====================

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню с основными разделами."""
    buttons = [
        [KeyboardButton(text="🛍️ Каталог")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="👥 Реферальная программа")],
        [KeyboardButton(text="⭐️ Отзывы"), KeyboardButton(text="🆘 Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ==================== ИНЛАЙН-КНОПКИ ====================

def get_catalog_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категории товаров."""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=f"📂 {category}", callback_data=f"category:{category}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_products_keyboard(products: List[tuple]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора товара в категории."""
    builder = InlineKeyboardBuilder()
    for product_id, name, price in products:
        builder.button(text=f"📦 {name} — {price}₽", callback_data=f"product:{product_id}")
    builder.button(text="🔙 Назад", callback_data="back_to_categories")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для конкретного товара."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Добавить в корзину", callback_data=f"add_to_cart:{product_id}")
    builder.button(text="🔙 Назад", callback_data="back_to_products")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для корзины."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data="checkout")
    builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    builder.button(text="🔙 В каталог", callback_data="back_to_categories")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора способа оплаты."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 YooKassa", callback_data="pay_yookassa")
    builder.button(text="📱 Telegram Payments", callback_data="pay_telegram")
    builder.button(text="🔙 Назад", callback_data="back_to_cart")
    builder.adjust(1)
    return builder.as_markup()

def get_referral_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для реферальной программы."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Получить реферальную ссылку", callback_data="get_referral_link")
    builder.button(text="📊 Моя статистика", callback_data="referral_stats")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для раздела поддержки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🆘 Написать в поддержку", url="https://t.me/support_username")
    builder.button(text="📖 FAQ", callback_data="faq")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_reviews_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для раздела отзывов."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐️ Оставить отзыв", callback_data="leave_review")
    builder.button(text="📖 Читать отзывы", callback_data="read_reviews")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# ==================== АДМИН-КЛАВИАТУРА ====================

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="✏️ Редактировать товар", callback_data="admin_edit_product")
    builder.button(text="🗑 Удалить товар", callback_data="admin_delete_product")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_edit_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования конкретного товара."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Изменить название", callback_data=f"edit_name:{product_id}")
    builder.button(text="💰 Изменить цену", callback_data=f"edit_price:{product_id}")
    builder.button(text="📂 Изменить категорию", callback_data=f"edit_category:{product_id}")
    builder.button(text="📄 Изменить описание", callback_data=f"edit_description:{product_id}")
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_confirm_keyboard(action: str, product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения для админ-действий."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=f"confirm_{action}:{product_id}")
    builder.button(text="❌ Отмена", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категории при добавлении/редактировании."""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=f"📂 {category}", callback_data=f"admin_category:{category}")
    builder.button(text="➕ Новая категория", callback_data="admin_new_category")
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()

# ==================== ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ ====================

def get_back_keyboard(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Универсальная клавиатура с кнопкой 'Назад'."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=callback_data)
    builder.button(text="❌ Нет", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()

def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура для пагинации."""
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️", callback_data=f"{prefix}:{page-1}")
    builder.button(text=f"{page}/{total_pages}", callback_data="current_page")
    if page < total_pages:
        builder.button(text="➡️", callback_data=f"{prefix}:{page+1}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(3)
    return builder.as_markup()

def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с методами оплаты."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 YooKassa", callback_data="pay_yookassa")
    builder.button(text="📱 Telegram Payments", callback_data="pay_telegram")
    builder.adjust(1)
    return builder.as_markup()

def get_success_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после успешной оплаты."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Получить товар", callback_data="get_product")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
