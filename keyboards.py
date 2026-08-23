from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional, List, Dict, Any

# ============================================
# ГЛАВНОЕ МЕНЮ (Reply-клавиатура)
# ============================================

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота с основными разделами"""
    buttons = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="👥 Реферальная программа")],
        [KeyboardButton(text="⭐️ Отзывы"), KeyboardButton(text="🆘 Поддержка")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел меню",
        selective=True,
    )


# ============================================
# ИНЛАЙН-КЛАВИАТУРЫ ДЛЯ КАТАЛОГА
# ============================================

def get_catalog_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура категорий товаров"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=f"📁 {category['name']}",
            callback_data=f"cat_{category['id']}"
        )
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_products_keyboard(
    products: List[Dict[str, Any]],
    category_id: int,
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """Клавиатура товаров в категории с пагинацией"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        builder.button(
            text=f"🛒 {product['name']} — {product['price']}₽",
            callback_data=f"prod_{product['id']}"
        )
    
    # Пагинация
    if total_pages > 1:
        pagination_row = []
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"page_{category_id}_{page-1}"
                )
            )
        pagination_row.append(
            InlineKeyboardButton(
                text=f"📄 {page}/{total_pages}",
                callback_data="noop"
            )
        )
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"page_{category_id}_{page+1}"
                )
            )
        builder.row(*pagination_row)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="back_to_catalog"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    builder.adjust(1)
    return builder.as_markup()


def get_product_detail_keyboard(
    product_id: int,
    in_cart: bool = False
) -> InlineKeyboardMarkup:
    """Клавиатура детальной страницы товара"""
    builder = InlineKeyboardBuilder()
    
    if in_cart:
        builder.button(
            text="✅ Уже в корзине",
            callback_data="noop"
        )
    else:
        builder.button(
            text="🛒 Добавить в корзину",
            callback_data=f"add_{product_id}"
        )
    
    builder.button(
        text="💳 Купить сейчас",
        callback_data=f"buy_{product_id}"
    )
    builder.button(
        text="⬅️ Назад к товарам",
        callback_data="back_to_products"
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()


# ============================================
# КЛАВИАТУРЫ ДЛЯ КОРЗИНЫ
# ============================================

def get_cart_keyboard(
    cart_items: List[Dict[str, Any]],
    total_price: float
) -> InlineKeyboardMarkup:
    """Клавиатура корзины с товарами"""
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {item['name']}",
                callback_data=f"remove_{item['id']}"
            )
        )
    
    if cart_items:
        builder.row(
            InlineKeyboardButton(
                text=f"💳 Оплатить {total_price}₽",
                callback_data="checkout"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data="clear_cart"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ В каталог", callback_data="back_to_catalog"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    builder.adjust(1)
    return builder.as_markup()


# ============================================
# КЛАВИАТУРЫ ДЛЯ РЕФЕРАЛЬНОЙ ПРОГРАММЫ
# ============================================

def get_referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🔗 Поделиться ссылкой",
        switch_inline_query=f"Присоединяйся к CyberMarket! {referral_link}"
    )
    builder.button(
        text="📊 Моя статистика",
        callback_data="referral_stats"
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()


# ============================================
# КЛАВИАТУРЫ ДЛЯ ОТЗЫВОВ
# ============================================

def get_reviews_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура раздела отзывов"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✍️ Оставить отзыв",
        callback_data="write_review"
    )
    builder.button(
        text="📖 Читать отзывы",
        callback_data="read_reviews"
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()


# ============================================
# КЛАВИАТУРЫ ДЛЯ ПОДДЕРЖКИ
# ============================================

def get_support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура раздела поддержки"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📝 Задать вопрос",
        callback_data="ask_support"
    )
    builder.button(
        text="📋 FAQ",
        callback_data="faq"
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()


# ============================================
# КЛАВИАТУРЫ ДЛЯ ОПЛАТЫ
# ============================================

def get_payment_keyboard(
    payment_url: Optional[str] = None,
    order_id: Optional[int] = None
) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    builder = InlineKeyboardBuilder()
    
    if payment_url:
        builder.button(
            text="💳 Перейти к оплате",
            url=payment_url
        )
    
    if order_id:
        builder.button(
            text="✅ Я оплатил",
            callback_data=f"confirm_payment_{order_id}"
        )
    
    builder.button(
        text="❌ Отменить оплату",
        callback_data="cancel_payment"
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_after_payment_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура после успешной оплаты"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📦 Получить товар",
        callback_data=f"get_product_{product_id}"
    )
    builder.button(
        text="📋 Мои покупки",
        callback_data="my_purchases"
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()


# ============================================
# АДМИН-КЛАВИАТУРЫ
# ============================================

def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📦 Управление товарами",
        callback_data="admin_products"
    )
    builder.button(
        text="📁 Управление категориями",
        callback_data="admin_categories"
    )
    builder.button(
        text="👥 Пользователи",
        callback_data="admin_users"
    )
    builder.button(
        text="📊 Статистика",
        callback_data="admin_stats"
    )
    builder.button(
        text="🏠 Выйти из админки",
        callback_data="main_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_admin_products_keyboard(
    products: List[Dict[str, Any]],
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """Клавиатура управления товарами для админа"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=f"✏️ {product['name']}",
                callback_data=f"admin_edit_{product['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"admin_delete_{product['id']}"
            )
        )
    
    # Пагинация
    if total_pages > 1:
        pagination_row = []
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"admin_page_{page-1}"
                )
            )
        pagination_row.append(
            InlineKeyboardButton(
                text=f"📄 {page}/{total_pages}",
                callback_data="noop"
            )
        )
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"admin_page_{page+1}"
                )
            )
        builder.row(*pagination_row)
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить товар",
            callback_data="admin_add_product"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админку",
            callback_data="admin_menu"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_admin_categories_keyboard(
    categories: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    """Клавиатура управления категориями для админа"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"✏️ {category['name']}",
                callback_data=f"admin_cat_edit_{category['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"admin_cat_delete_{category['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить категорию",
            callback_data="admin_add_category"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админку",
            callback_data="admin_menu"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_admin_edit_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура редактирования товара"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📝 Изменить название",
        callback_data=f"edit_name_{product_id}"
    )
    builder.button(
        text="💰 Изменить цену",
        callback_data=f"edit_price_{product_id}"
    )
    builder.button(
        text="📄 Изменить описание",
        callback_data=f"edit_desc_{product_id}"
    )
    builder.button(
        text="🔗 Изменить ссылку",
        callback_data=f"edit_link_{product_id}"
    )
    builder.button(
        text="📁 Изменить категорию",
        callback_data=f"edit_cat_{product_id}"
    )
    builder.button(
        text="⬅️ Назад к товарам",
        callback_data="admin_products"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✅ Подтвердить",
        callback_data=f"confirm_{action}_{item_id}"
    )
    builder.button(
        text="❌ Отмена",
        callback_data=f"cancel_{action}"
    )
    
    builder.adjust(2)
    return builder.as_markup()


# ============================================
# ОБЩИЕ КЛАВИАТУРЫ
# ============================================

def get_back_keyboard(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Универсальная клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ Назад",
        callback_data=callback_data
    )
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_inline() -> InlineKeyboardMarkup:
    """Инлайн-версия главного меню"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🛍 Каталог",
        callback_data="back_to_catalog"
    )
    builder.button(
        text="🛒 Корзина",
        callback_data="view_cart"
    )
    builder.button(
        text="👥 Реферальная программа",
        callback_data="referral"
    )
    builder.button(
        text="⭐️ Отзывы",
        callback_data="reviews"
    )
    builder.button(
        text="🆘 Поддержка",
        callback_data="support"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_noop_keyboard() -> InlineKeyboardMarkup:
    """Заглушка для неактивных кнопок"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏳ Обработка...",
        callback_data="noop"
    )
    builder.adjust(1)
    return builder.as_markup()
