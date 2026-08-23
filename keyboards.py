# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ================== ГЛАВНОЕ МЕНЮ ==================
def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🛍 Каталог")
    kb.button(text="🛒 Корзина")
    kb.button(text="👥 Реферальная программа")
    kb.button(text="⭐️ Отзывы")
    kb.button(text="🆘 Поддержка")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


# ================== КАТАЛОГ ==================
def catalog_categories_kb(categories: list[str]) -> InlineKeyboardMarkup:
    """Кнопки категорий товаров"""
    kb = InlineKeyboardBuilder()
    for category in categories:
        kb.button(text=category, callback_data=f"cat_{category}")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def products_kb(products: list[tuple[int, str, float]]) -> InlineKeyboardMarkup:
    """Кнопки товаров в категории"""
    kb = InlineKeyboardBuilder()
    for product_id, name, price in products:
        kb.button(
            text=f"{name} — {price} ₽",
            callback_data=f"product_{product_id}"
        )
    kb.button(text="⬅️ Назад", callback_data="back_to_categories")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    """Кнопки для конкретного товара"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Добавить в корзину", callback_data=f"add_{product_id}")
    kb.button(text="⬅️ Назад", callback_data="back_to_products")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


# ================== КОРЗИНА ==================
def cart_kb() -> InlineKeyboardMarkup:
    """Кнопки корзины"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплатить", callback_data="checkout")
    kb.button(text="🗑 Очистить", callback_data="clear_cart")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def cart_item_kb(product_id: int) -> InlineKeyboardMarkup:
    """Кнопки для товара в корзине"""
    kb = InlineKeyboardBuilder()
    kb.button(text="➖", callback_data=f"dec_{product_id}")
    kb.button(text="➕", callback_data=f"inc_{product_id}")
    kb.button(text="❌", callback_data=f"remove_{product_id}")
    kb.adjust(3)
    return kb.as_markup()


# ================== РЕФЕРАЛЬНАЯ ПРОГРАММА ==================
def referral_kb() -> InlineKeyboardMarkup:
    """Кнопки реферальной программы"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔗 Получить реферальную ссылку", callback_data="get_ref_link")
    kb.button(text="💰 Мои бонусы", callback_data="my_bonuses")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


# ================== ОТЗЫВЫ ==================
def reviews_kb() -> InlineKeyboardMarkup:
    """Кнопки раздела отзывов"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Оставить отзыв", callback_data="write_review")
    kb.button(text="📖 Читать отзывы", callback_data="read_reviews")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


# ================== ПОДДЕРЖКА ==================
def support_kb() -> InlineKeyboardMarkup:
    """Кнопки раздела поддержки"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📨 Написать в поддержку", callback_data="contact_support")
    kb.button(text="❓ FAQ", callback_data="faq")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


# ================== ОПЛАТА ==================
def payment_kb(payment_url: str, order_id: int) -> InlineKeyboardMarkup:
    """Кнопки оплаты"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплатить", url=payment_url)
    kb.button(text="✅ Я оплатил", callback_data=f"check_payment_{order_id}")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


# ================== АДМИН-ПАНЕЛЬ ==================
def admin_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Добавить товар", callback_data="admin_add_product")
    kb.button(text="✏️ Редактировать товар", callback_data="admin_edit_product")
    kb.button(text="🗑 Удалить товар", callback_data="admin_delete_product")
    kb.button(text="📊 Статистика", callback_data="admin_stats")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_products_kb(products: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Список товаров для админа"""
    kb = InlineKeyboardBuilder()
    for product_id, name in products:
        kb.button(text=name, callback_data=f"admin_select_{product_id}")
    kb.button(text="⬅️ Назад", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()


def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    """Действия с товаром для админа"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Изменить название", callback_data=f"edit_name_{product_id}")
    kb.button(text="📝 Изменить описание", callback_data=f"edit_desc_{product_id}")
    kb.button(text="💰 Изменить цену", callback_data=f"edit_price_{product_id}")
    kb.button(text="📂 Изменить файл", callback_data=f"edit_file_{product_id}")
    kb.button(text="🔗 Изменить ссылку", callback_data=f"edit_link_{product_id}")
    kb.button(text="📁 Изменить категорию", callback_data=f"edit_cat_{product_id}")
    kb.button(text="⬅️ Назад", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()


def admin_confirm_kb(action: str, product_id: int) -> InlineKeyboardMarkup:
    """Подтверждение действия админа"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data=f"confirm_{action}_{product_id}")
    kb.button(text="❌ Отмена", callback_data="admin_cancel")
    kb.adjust(1)
    return kb.as_markup()


def admin_cancel_kb() -> InlineKeyboardMarkup:
    """Отмена действия"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data="admin_cancel")
    kb.adjust(1)
    return kb.as_markup()


# ================== ОБЩИЕ ==================
def back_to_main_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def confirm_order_kb() -> InlineKeyboardMarkup:
    """Подтверждение заказа"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить заказ", callback_data="confirm_order")
    kb.button(text="❌ Отменить", callback_data="cancel_order")
    kb.adjust(1)
    return kb.as_markup()
