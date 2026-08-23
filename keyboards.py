from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional, List


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    buttons = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="👥 Реферальная программа")],
        [KeyboardButton(text="⭐️ Отзывы"), KeyboardButton(text="🆘 Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def catalog_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category, callback_data=f"category:{category}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()


def products_keyboard(products: List[dict], category: str, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура с товарами в категории"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        product_id = product.get("product_id")
        name = product.get("name", "Товар")
        price = product.get("price", 0)
        builder.button(
            text=f"💰 {name} — {price}₽",
            callback_data=f"product:{product_id}"
        )
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page:{category}:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page:{category}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def product_detail_keyboard(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра товара"""
    builder = InlineKeyboardBuilder()
    
    if not in_cart:
        builder.button(text="🛒 Добавить в корзину", callback_data=f"add_to_cart:{product_id}")
    
    builder.button(text="⬅️ Назад", callback_data="back_to_catalog")
    builder.button(text="🛒 Корзина", callback_data="view_cart")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    return builder.as_markup()


def cart_keyboard(cart_items: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        product_id = item.get("product_id")
        name = item.get("name", "Товар")
        price = item.get("price", 0)
        quantity = item.get("quantity", 1)
        builder.button(
            text=f"❌ {name} x{quantity} — {price * quantity}₽",
            callback_data=f"remove_from_cart:{product_id}"
        )
    
    builder.row(
        InlineKeyboardButton(text="💳 Оплатить", callback_data="checkout"),
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_catalog"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def payment_keyboard(order_id: int, payment_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    builder = InlineKeyboardBuilder()
    
    if payment_url:
        builder.button(text="💳 Оплатить", url=payment_url)
    
    builder.button(text="✅ Я оплатил", callback_data=f"check_payment:{order_id}")
    builder.button(text="❌ Отменить", callback_data="cancel_payment")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    return builder.as_markup()


def referral_keyboard(referral_code: str) -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📤 Поделиться", switch_inline_query=f"Присоединяйся по реферальной ссылке! Код: {referral_code}")
    builder.button(text="💰 Мои бонусы", callback_data="my_bonuses")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    return builder.as_markup()


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📦 Добавить товар", callback_data="admin_add_product")
    builder.button(text="✏️ Редактировать товар", callback_data="admin_edit_product")
    builder.button(text="🗑 Удалить товар", callback_data="admin_delete_product")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2)
    
    return builder.as_markup()


def admin_products_list_keyboard(products: List[dict], action: str) -> InlineKeyboardMarkup:
    """Клавиатура списка товаров для админа"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        product_id = product.get("product_id")
        name = product.get("name", "Товар")
        builder.button(
            text=f"{name}",
            callback_data=f"admin_{action}:{product_id}"
        )
    
    builder.button(text="⬅️ Назад", callback_data="admin_back")
    builder.adjust(1)
    
    return builder.as_markup()


def admin_edit_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура редактирования товара"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📝 Название", callback_data=f"edit_name:{product_id}")
    builder.button(text="📄 Описание", callback_data=f"edit_description:{product_id}")
    builder.button(text="💰 Цена", callback_data=f"edit_price:{product_id}")
    builder.button(text="📂 Категория", callback_data=f"edit_category:{product_id}")
    builder.button(text="📎 Файл", callback_data=f"edit_file:{product_id}")
    builder.button(text="🔗 Ссылка", callback_data=f"edit_link:{product_id}")
    builder.button(text="✅ Готово", callback_data="admin_back")
    builder.adjust(2)
    
    return builder.as_markup()


def confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Подтвердить", callback_data=f"confirm_{action}:{item_id}")
    builder.button(text="❌ Отмена", callback_data="admin_back")
    builder.adjust(2)
    
    return builder.as_markup()


def support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поддержки"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📝 Задать вопрос", callback_data="ask_question")
    builder.button(text="📞 Связаться с админом", callback_data="contact_admin")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    return builder.as_markup()


def reviews_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отзывов"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="⭐️ Оставить отзыв", callback_data="leave_review")
    builder.button(text="📖 Читать отзывы", callback_data="read_reviews")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    return builder.as_markup()


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    return builder.as_markup()
