# keyboards.py
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict, Any
from config import settings


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    buttons = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="👥 Рефералка")],
        [KeyboardButton(text="⭐ Отзывы")],
        [KeyboardButton(text="🆘 Поддержка")]
    ]
    
    if is_admin:
        buttons.append([KeyboardButton(text="👨💻 Админ-панель")])
    
    kb = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    return kb


def categories_kb(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров"""
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 {cat['name']}",
                callback_data=f"cat_{cat['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_kb(products: List[Dict[str, Any]], category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с товарами категории"""
    buttons = []
    for prod in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"🛍 {prod['name']} — {prod['price']}₽",
                callback_data=f"prod_{prod['id']}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{category_id}"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_card_kb(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура карточки товара"""
    buttons = [
        [
            InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_{product_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{category_id}"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_kb(cart_items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    buttons = []
    for item in cart_items:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ Удалить: {item['name']}",
                callback_data=f"del_{item['id']}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="💳 Оплатить", callback_data="checkout")
    ])
    buttons.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_categories_kb(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории для админа"""
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 {cat['name']}",
                callback_data=f"admin_cat_{cat['id']}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_add_product_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения добавления товара"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="admin_confirm_add")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def referral_kb(referral_link: str) -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы"""
    buttons = [
        [
            InlineKeyboardButton(text="🔗 Поделиться ссылкой", url=referral_link)
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def support_kb() -> InlineKeyboardMarkup:
    """Клавиатура поддержки"""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Написать в поддержку", url="https://t.me/support")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def reviews_kb() -> InlineKeyboardMarkup:
    """Клавиатура отзывов"""
    buttons = [
        [
            InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="leave_review")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def checkout_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения оплаты"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data="confirm_payment")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="view_cart")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_success_kb() -> InlineKeyboardMarkup:
    """Клавиатура после успешной оплаты"""
    buttons = [
        [
            InlineKeyboardButton(text="🛍 Продолжить покупки", callback_data="catalog")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
