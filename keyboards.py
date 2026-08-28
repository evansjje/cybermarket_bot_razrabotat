# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import List, Optional
from config import settings

# Callback data factories
class CategoryCallback(CallbackData, prefix="cat"):
    action: str
    cat_id: Optional[int] = None

class ProductCallback(CallbackData, prefix="prod"):
    action: str
    product_id: Optional[int] = None
    cat_id: Optional[int] = None

class CartCallback(CallbackData, prefix="cart"):
    action: str

class AdminCallback(CallbackData, prefix="admin"):
    action: str
    cat_id: Optional[int] = None
    product_id: Optional[int] = None

# Main menu keyboard
def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text='🛍 Каталог'), KeyboardButton(text='🛒 Корзина')],
        [KeyboardButton(text='👥 Рефералка'), KeyboardButton(text='⭐ Отзывы')],
        [KeyboardButton(text='🆘 Поддержка')]
    ]
    
    if user_id in settings.ADMIN_IDS:
        keyboard.append([KeyboardButton(text='⚡ Админ-панель')])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

# Categories inline keyboard
def get_categories_keyboard(categories: List[dict], user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    
    for cat in categories:
        cat_id = cat.get('id', 0)
        title = cat.get('title', 'Без названия')
        
        row = [
            InlineKeyboardButton(
                text=title,
                callback_data=CategoryCallback(action='view', cat_id=cat_id).pack()
            )
        ]
        
        if user_id in settings.ADMIN_IDS:
            row.append(
                InlineKeyboardButton(
                    text='✏️',
                    callback_data=AdminCallback(action='edit_cat', cat_id=cat_id).pack()
                )
            )
            row.append(
                InlineKeyboardButton(
                    text='🗑',
                    callback_data=AdminCallback(action='del_cat', cat_id=cat_id).pack()
                )
            )
        
        buttons.append(row)
    
    if user_id in settings.ADMIN_IDS:
        buttons.append([
            InlineKeyboardButton(
                text='➕ Добавить категорию',
                callback_data=AdminCallback(action='add_cat').pack()
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text='🏠 Главное меню',
            callback_data=CategoryCallback(action='main').pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Products inline keyboard
def get_products_keyboard(products: List[dict], cat_id: int, user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    
    for product in products:
        product_id = product.get('id', 0)
        title = product.get('title', 'Без названия')
        price = product.get('price', 0)
        
        row = [
            InlineKeyboardButton(
                text=f"{title} — {price}₽",
                callback_data=ProductCallback(action='view', product_id=product_id, cat_id=cat_id).pack()
            )
        ]
        
        if user_id in settings.ADMIN_IDS:
            row.append(
                InlineKeyboardButton(
                    text='✏️',
                    callback_data=AdminCallback(action='edit_prod', product_id=product_id, cat_id=cat_id).pack()
                )
            )
            row.append(
                InlineKeyboardButton(
                    text='🗑',
                    callback_data=AdminCallback(action='del_prod', product_id=product_id, cat_id=cat_id).pack()
                )
            )
        
        buttons.append(row)
    
    if user_id in settings.ADMIN_IDS:
        buttons.append([
            InlineKeyboardButton(
                text='➕ Добавить товар',
                callback_data=AdminCallback(action='add_prod', cat_id=cat_id).pack()
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data=CategoryCallback(action='back', cat_id=cat_id).pack()
        ),
        InlineKeyboardButton(
            text='🏠 Главное меню',
            callback_data=CategoryCallback(action='main').pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Product detail keyboard
def get_product_detail_keyboard(product_id: int, cat_id: int, user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text='➕ В корзину',
                callback_data=ProductCallback(action='add', product_id=product_id, cat_id=cat_id).pack()
            )
        ]
    ]
    
    if user_id in settings.ADMIN_IDS:
        buttons.append([
            InlineKeyboardButton(
                text='✏️ Редактировать',
                callback_data=AdminCallback(action='edit_prod', product_id=product_id, cat_id=cat_id).pack()
            ),
            InlineKeyboardButton(
                text='🗑 Удалить',
                callback_data=AdminCallback(action='del_prod', product_id=product_id, cat_id=cat_id).pack()
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data=CategoryCallback(action='view', cat_id=cat_id).pack()
        ),
        InlineKeyboardButton(
            text='🏠 Главное меню',
            callback_data=CategoryCallback(action='main').pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Cart keyboard
def get_cart_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text='🗑 Очистить корзину',
                callback_data=CartCallback(action='clear').pack()
            ),
            InlineKeyboardButton(
                text='💳 Оплатить',
                callback_data=CartCallback(action='pay').pack()
            )
        ],
        [
            InlineKeyboardButton(
                text='🛍 Продолжить покупки',
                callback_data=CategoryCallback(action='main').pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Admin panel keyboard
def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text='📊 Статистика',
                callback_data=AdminCallback(action='stats').pack()
            )
        ],
        [
            InlineKeyboardButton(
                text='➕ Добавить категорию',
                callback_data=AdminCallback(action='add_cat').pack()
            )
        ],
        [
            InlineKeyboardButton(
                text='🏠 Главное меню',
                callback_data=CategoryCallback(action='main').pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Cancel keyboard for FSM
def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='❌ Отмена',
                    callback_data=AdminCallback(action='cancel').pack()
                )
            ]
        ]
    )

# Admin edit product keyboard
def get_admin_edit_product_keyboard(product_id: int, cat_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text='💰 Изменить цену',
                callback_data=AdminCallback(action='edit_price', product_id=product_id, cat_id=cat_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text='📝 Изменить описание',
                callback_data=AdminCallback(action='edit_desc', product_id=product_id, cat_id=cat_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text='⬅️ Назад',
                callback_data=CategoryCallback(action='view', cat_id=cat_id).pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
