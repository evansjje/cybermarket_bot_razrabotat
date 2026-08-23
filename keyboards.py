# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    buttons = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="👥 Рефералка")],
        [KeyboardButton(text="⭐ Отзывы"), KeyboardButton(text="🆘 Поддержка")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="📦 Список товаров", callback_data="admin_products")
    builder.button(text="🔙 Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def categories_kb(categories: list) -> InlineKeyboardMarkup:
    """Клавиатура категорий товаров."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat["name"], callback_data=f"cat_{cat['id']}")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def products_kb(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура товаров в категории."""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(text=f"{prod['name']} — {prod['price']}₽", callback_data=f"prod_{prod['id']}")
    builder.button(text="🔙 Назад", callback_data=f"back_to_cat_{category_id}")
    builder.button(text="🏠 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def product_card_kb(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура карточки товара."""
    builder = InlineKeyboardBuilder()
    if in_cart:
        builder.button(text="✅ В корзине", callback_data="already_in_cart")
    else:
        builder.button(text="🛒 Добавить в корзину", callback_data=f"add_{product_id}")
    builder.button(text="🔙 Назад", callback_data="back_to_catalog")
    builder.button(text="🏠 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def cart_kb(cart_items: list) -> InlineKeyboardMarkup:
    """Клавиатура корзины с товарами."""
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        builder.button(
            text=f"❌ Удалить: {item['name']}",
            callback_data=f"del_{item['product_id']}"
        )
    builder.button(text="💳 Перейти к оплате", callback_data="checkout")
    builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def checkout_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения оплаты."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить заказ", callback_data="confirm_order")
    builder.button(text="❌ Отменить", callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()


def referral_kb() -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Поделиться ссылкой", switch_inline_query="Присоединяйся к CyberMarket!")
    builder.button(text="🏠 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def support_kb() -> InlineKeyboardMarkup:
    """Клавиатура поддержки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Написать в поддержку", url="https://t.me/support")
    builder.button(text="🏠 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def reviews_kb() -> InlineKeyboardMarkup:
    """Клавиатура отзывов."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Оставить отзыв", callback_data="leave_review")
    builder.button(text="📖 Читать отзывы", callback_data="read_reviews")
    builder.button(text="🏠 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    """Клавиатура списка товаров для админа."""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod['name']} — {prod['price']}₽ (остаток: {prod['stock']})",
            callback_data=f"admin_prod_{prod['id']}"
        )
    builder.button(text="🔙 Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с товаром для админа."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить цену", callback_data=f"edit_price_{product_id}")
    builder.button(text="📦 Изменить остаток", callback_data=f"edit_stock_{product_id}")
    builder.button(text="🗑 Удалить товар", callback_data=f"delete_prod_{product_id}")
    builder.button(text="🔙 Назад", callback_data="admin_products")
    builder.adjust(1)
    return builder.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    """Клавиатура возврата в админ-панель."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В админ-панель", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура возврата в главное меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def confirm_order_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить заказ", callback_data="confirm_order")
    builder.button(text="❌ Отменить", callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()


def back_to_categories_kb() -> InlineKeyboardMarkup:
    """Клавиатура возврата к категориям."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К категориям", callback_data="back_to_catalog")
    builder.adjust(1)
    return builder.as_markup()
