# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import settings


def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛍 Каталог"),
        KeyboardButton(text="🛒 Корзина")
    )
    builder.row(
        KeyboardButton(text="👥 Рефералка"),
        KeyboardButton(text="⭐ Отзывы")
    )
    builder.row(
        KeyboardButton(text="🆘 Поддержка")
    )
    if user_id in settings.ADMIN_IDS:
        builder.row(
            KeyboardButton(text="⚡ Админ-панель")
        )
    return builder.as_markup(resize_keyboard=True)


def categories_kb(categories: list) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура категорий"""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat[1],
            callback_data=f"cat_{cat[0]}"
        )
    builder.adjust(1)
    return builder.as_markup()


def products_kb(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура товаров категории"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod[2]} — {prod[4]} ₽",
            callback_data=f"prod_{prod[0]}"
        )
    builder.button(
        text="⬅️ Назад",
        callback_data=f"back_cat_{category_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def product_card_kb(product_id: int) -> InlineKeyboardMarkup:
    """Карточка товара с кнопкой добавления в корзину"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ В корзину",
        callback_data=f"add_{product_id}"
    )
    builder.button(
        text="⬅️ Назад",
        callback_data="back_products"
    )
    builder.adjust(1)
    return builder.as_markup()


def cart_kb(cart_items: list) -> InlineKeyboardMarkup:
    """Корзина с товарами и управлением количеством"""
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        product_id = item[1]
        count = item[2]
        builder.row(
            InlineKeyboardButton(
                text="➖",
                callback_data=f"dec_{product_id}"
            ),
            InlineKeyboardButton(
                text=f"{count} шт.",
                callback_data="noop"
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"inc_{product_id}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"del_{product_id}"
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Очистить",
            callback_data="clear_cart"
        ),
        InlineKeyboardButton(
            text="💳 Оплатить",
            callback_data="checkout"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ В каталог",
            callback_data="back_to_catalog"
        )
    )
    return builder.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    """Админ-панель"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📊 Статистика",
        callback_data="admin_stats"
    )
    builder.button(
        text="➕ Добавить товар",
        callback_data="admin_add_product"
    )
    builder.button(
        text="📦 Список товаров",
        callback_data="admin_products"
    )
    builder.button(
        text="📋 Заказы",
        callback_data="admin_orders"
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_add_product_kb() -> InlineKeyboardMarkup:
    """Подтверждение добавления товара"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data="confirm_add_product"
    )
    builder.button(
        text="❌ Отмена",
        callback_data="cancel_add_product"
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    """Список товаров для админа"""
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod[2]} — {prod[4]} ₽",
            callback_data=f"admin_prod_{prod[0]}"
        )
    builder.button(
        text="⬅️ Назад",
        callback_data="admin_back"
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    """Действия с товаром для админа"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🗑 Удалить",
        callback_data=f"admin_del_{product_id}"
    )
    builder.button(
        text="⬅️ Назад",
        callback_data="admin_products"
    )
    builder.adjust(1)
    return builder.as_markup()


def payment_kb(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Оплатил",
        callback_data=f"pay_{order_id}"
    )
    builder.button(
        text="❌ Отмена",
        callback_data="cancel_payment"
    )
    builder.adjust(1)
    return builder.as_markup()


def back_to_catalog_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в каталог"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ В каталог",
        callback_data="back_to_catalog"
    )
    return builder.as_markup()


def reviews_kb() -> InlineKeyboardMarkup:
    """Клавиатура для раздела отзывов"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✍️ Оставить отзыв",
        callback_data="write_review"
    )
    builder.button(
        text="📖 Все отзывы",
        callback_data="all_reviews"
    )
    builder.button(
        text="⬅️ Назад",
        callback_data="back_to_menu"
    )
    builder.adjust(1)
    return builder.as_markup()


def referrals_kb() -> InlineKeyboardMarkup:
    """Клавиатура для раздела реферальной системы"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔗 Моя ссылка",
        callback_data="my_referral"
    )
    builder.button(
        text="💰 Баланс",
        callback_data="referral_balance"
    )
    builder.button(
        text="⬅️ Назад",
        callback_data="back_to_menu"
    )
    builder.adjust(1)
    return builder.as_markup()


def support_kb() -> InlineKeyboardMarkup:
    """Клавиатура для раздела поддержки"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📝 Написать в поддержку",
        callback_data="write_support"
    )
    builder.button(
        text="❓ FAQ",
        callback_data="faq"
    )
    builder.button(
        text="⬅️ Назад",
        callback_data="back_to_menu"
    )
    builder.adjust(1)
    return builder.as_markup()
