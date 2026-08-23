from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛍 Каталог"),
                KeyboardButton(text="🛒 Корзина")
            ],
            [
                KeyboardButton(text="👥 Реферальная программа"),
                KeyboardButton(text="⭐️ Отзывы")
            ],
            [
                KeyboardButton(text="🆘 Поддержка")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    return keyboard


def catalog_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category,
            callback_data=f"category:{category}"
        )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products: list[tuple[int, str, float]], category: str) -> InlineKeyboardMarkup:
    """Клавиатура с товарами в категории"""
    builder = InlineKeyboardBuilder()
    for product_id, name, price in products:
        builder.button(
            text=f"{name} - {price}₽",
            callback_data=f"product:{product_id}"
        )
    builder.button(
        text="🔙 Назад к категориям",
        callback_data="back_to_catalog"
    )
    builder.adjust(1)
    return builder.as_markup()


def product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра товара"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛒 Добавить в корзину",
        callback_data=f"add_to_cart:{product_id}"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_catalog"
    )
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для корзины"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 Оплатить",
        callback_data="checkout"
    )
    builder.button(
        text="🗑 Очистить корзину",
        callback_data="clear_cart"
    )
    builder.button(
        text="🔙 В меню",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 Перейти к оплате",
        url=payment_url
    )
    builder.button(
        text="✅ Я оплатил",
        callback_data="payment_confirmed"
    )
    builder.button(
        text="🔙 Отменить",
        callback_data="cancel_payment"
    )
    builder.adjust(1)
    return builder.as_markup()


def referral_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для реферальной программы"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔗 Получить реферальную ссылку",
        callback_data="get_referral_link"
    )
    builder.button(
        text="👥 Мои рефералы",
        callback_data="my_referrals"
    )
    builder.button(
        text="🔙 В меню",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📦 Управление товарами",
        callback_data="admin_products"
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
        text="🔙 В меню",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_products_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления товарами"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Добавить товар",
        callback_data="admin_add_product"
    )
    builder.button(
        text="✏️ Редактировать товар",
        callback_data="admin_edit_product"
    )
    builder.button(
        text="🗑 Удалить товар",
        callback_data="admin_delete_product"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="admin_back"
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_product_list_keyboard(products: list[tuple[int, str, float]], action: str) -> InlineKeyboardMarkup:
    """Клавиатура со списком товаров для админа"""
    builder = InlineKeyboardBuilder()
    for product_id, name, price in products:
        builder.button(
            text=f"{name} - {price}₽",
            callback_data=f"admin_{action}:{product_id}"
        )
    builder.button(
        text="🔙 Назад",
        callback_data="admin_products"
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_edit_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура редактирования товара"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📝 Название",
        callback_data=f"edit_name:{product_id}"
    )
    builder.button(
        text="📄 Описание",
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
        text="📝 Контент",
        callback_data=f"edit_content:{product_id}"
    )
    builder.button(
        text="✅ Завершить",
        callback_data="admin_products"
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=f"confirm_{action}:{item_id}"
    )
    builder.button(
        text="❌ Отмена",
        callback_data=f"cancel_{action}"
    )
    builder.adjust(2)
    return builder.as_markup()


def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата в админку"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔙 В админ-панель",
        callback_data="admin_back"
    )
    return builder.as_markup()
