from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import settings
from database import get_categories, get_products_by_category, get_cart_items, get_product


def main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="🛒 Корзина"))
    builder.row(KeyboardButton(text="👥 Рефералка"), KeyboardButton(text="⭐ Отзывы"))
    builder.row(KeyboardButton(text="🆘 Поддержка"))
    if user_id in settings.ADMIN_IDS:
        builder.row(KeyboardButton(text="⚡ Админ-панель"))
    return builder.as_markup(resize_keyboard=True)


async def categories_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    builder = InlineKeyboardBuilder()
    categories = await get_categories()
    for cat in categories:
        builder.button(text=cat[1], callback_data=f"cat_{cat[0]}")
    builder.adjust(2)
    return builder.as_markup()


async def products_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    builder = InlineKeyboardBuilder()
    products = await get_products_by_category(category_id)
    for prod in products:
        builder.button(text=prod[2], callback_data=f"prod_{prod[0]}")
    builder.button(text="⬅️ Назад", callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


async def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура карточки товара"""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ В корзину", callback_data=f"add_{product_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_products")
    builder.adjust(1)
    return builder.as_markup()


async def cart_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()
    cart_items = await get_cart_items(user_id)
    for item in cart_items:
        product = await get_product(item[1])
        if product:
            builder.button(
                text=f"➖ {product[2]}",
                callback_data=f"dec_{item[1]}"
            )
            builder.button(
                text=f"➕ {product[2]}",
                callback_data=f"inc_{item[1]}"
            )
            builder.button(
                text=f"❌ {product[2]}",
                callback_data=f"del_{item[1]}"
            )
    builder.button(text="💳 Оплатить", callback_data="checkout")
    builder.button(text="🗑 Очистить", callback_data="clear_cart")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(3)
    return builder.as_markup()


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📊 Статистика"))
    builder.row(KeyboardButton(text="➕ Добавить товар"))
    builder.row(KeyboardButton(text="📦 Список товаров"))
    builder.row(KeyboardButton(text="⬅️ Назад"))
    return builder.as_markup(resize_keyboard=True)


def admin_products_keyboard(products: list) -> InlineKeyboardMarkup:
    """Клавиатура списка товаров для админа"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"❌ {prod[2]}",
            callback_data=f"admin_del_{prod[0]}"
        )
    builder.button(text="⬅️ Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


# ===== Недостающие функции =====

def admin_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления категориями для админа"""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить категорию", callback_data="admin_add_category")
    builder.button(text="🗑 Удалить категорию", callback_data="admin_del_category")
    builder.button(text="⬅️ Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поддержки"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Задать вопрос", callback_data="support_question")
    builder.button(text="📞 Связаться с оператором", callback_data="support_operator")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def reviews_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отзывов"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Оставить отзыв", callback_data="add_review")
    builder.button(text="📖 Все отзывы", callback_data="all_reviews")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с товаром для админа"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить", callback_data=f"admin_edit_{product_id}")
    builder.button(text="🗑 Удалить", callback_data=f"admin_del_{product_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_products")
    builder.adjust(2)
    return builder.as_markup()


def admin_panel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура админ-панели (алиас для admin_menu_keyboard)"""
    return admin_menu_keyboard()


def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Алиас для main_menu_keyboard"""
    return main_menu_keyboard(user_id)


def referral_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура реферальной системы"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Моя ссылка", callback_data="my_referral_link")
    builder.button(text="👥 Мои рефералы", callback_data="my_referrals")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def cart_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура действий с корзиной"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data="checkout")
    builder.button(text="🗑 Очистить", callback_data="clear_cart")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()
