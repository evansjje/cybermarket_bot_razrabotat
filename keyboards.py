from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Main menu keyboard
def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="👥 Реферальная программа")],
        [KeyboardButton(text="⭐️ Отзывы"), KeyboardButton(text="📞 Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Catalog keyboard
def catalog_kb(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat, callback_data=f"cat_{cat}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Products keyboard
def products_kb(products: list, category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=product[1], callback_data=f"prod_{product[0]}")
    builder.button(text="⬅️ Назад", callback_data=f"back_{category}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Product detail keyboard
def product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Добавить в корзину", callback_data=f"add_{product_id}")
    builder.button(text="⬅️ Назад", callback_data="back_catalog")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Cart keyboard
def cart_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data="checkout")
    builder.button(text="🗑 Очистить", callback_data="clear_cart")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Payment keyboard
def payment_kb(payment_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", url=payment_url)
    builder.button(text="✅ Я оплатил", callback_data="check_payment")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Referral keyboard
def referral_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Поделиться ссылкой", switch_inline_query="Присоединяйся к CyberMarket!")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Admin panel keyboard
def admin_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="admin_add")
    builder.button(text="✏️ Редактировать", callback_data="admin_edit")
    builder.button(text="❌ Удалить", callback_data="admin_delete")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Admin product management keyboard
def admin_products_kb(products: list, action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=product[1], callback_data=f"admin_{action}_{product[0]}")
    builder.button(text="⬅️ Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()

# Admin edit product keyboard
def admin_edit_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Название", callback_data=f"edit_name_{product_id}")
    builder.button(text="📄 Описание", callback_data=f"edit_desc_{product_id}")
    builder.button(text="💰 Цена", callback_data=f"edit_price_{product_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()

# Confirmation keyboard
def confirm_kb(action: str, product_id: int = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=f"confirm_{action}_{product_id}" if product_id else f"confirm_{action}")
    builder.button(text="❌ Нет", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()

# Support keyboard
def support_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Связаться с поддержкой", url="https://t.me/support")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
