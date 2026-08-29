# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart

from config import settings
from database import db
from keyboards import admin_menu, main_menu, products_admin_keyboard

router = Router()


class CategoryForm(StatesGroup):
    title = State()


class ProductForm(StatesGroup):
    category_id = State()
    title = State()
    desc = State()
    price = State()


class EditPriceForm(StatesGroup):
    price = State()


class EditDescForm(StatesGroup):
    desc = State()


@router.message(F.text == '⚡ Админ-панель')
@router.message(Command('admin'))
async def admin_panel(message: Message) -> None:
    """Открытие админ-панели"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer('⛔️ У вас нет доступа к админ-панели')
        return

    await message.answer(
        '⚡ Админ-панель\n\nВыберите действие:',
        reply_markup=admin_menu()
    )


@router.message(F.text == '⬅️ Назад')
async def back_to_main(message: Message) -> None:
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    await message.answer(
        'Главное меню:',
        reply_markup=main_menu(is_admin=is_admin)
    )


@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message) -> None:
    """Показ статистики"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer('⛔️ У вас нет доступа к админ-панели')
        return

    stats = await db.get_stats()
    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📦 Товаров: <b>{stats['products']}</b>\n"
        f"📂 Категорий: <b>{stats['categories']}</b>\n"
        f"🛒 Заказов: <b>{stats['orders']}</b>"
    )
    await message.answer(text)


@router.message(F.text == '➕ Категория')
async def add_category_start(message: Message, state: FSMContext) -> None:
    """Начало добавления категории"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer('⛔️ У вас нет доступа к админ-панели')
        return

    await state.set_state(CategoryForm.title)
    await message.answer(
        '📝 Введите название новой категории:\n\n'
        'Для отмены отправьте /cancel'
    )


@router.message(CategoryForm.title)
async def add_category_title(message: Message, state: FSMContext) -> None:
    """Получение названия категории"""
    title = message.text.strip()

    if not title:
        await message.answer('❌ Название не может быть пустым. Попробуйте ещё раз:')
        return

    try:
        await db.add_category(title)
        await state.clear()
        await message.answer(
            f'✅ Категория «{title}» успешно добавлена!',
            reply_markup=admin_menu()
        )
    except Exception:
        await message.answer(
            '❌ Такая категория уже существует или произошла ошибка.\n'
            'Попробуйте другое название:'
        )


@router.message(F.text == '➕ Товар')
async def add_product_start(message: Message, state: FSMContext) -> None:
    """Начало добавления товара"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer('⛔️ У вас нет доступа к админ-панели')
        return

    categories = await db.get_categories()
    if not categories:
        await message.answer(
            '❌ Сначала добавьте хотя бы одну категорию!',
            reply_markup=admin_menu()
        )
        return

    await state.set_state(ProductForm.category_id)
    await message.answer(
        '📂 Выберите категорию для товара:\n\n'
        'Для отмены отправьте /cancel'
    )

    # Показываем категории инлайн-кнопками
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat['title'],
            callback_data=f"admin_cat_{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Отмена', callback_data='admin_cancel')])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer('Категории:', reply_markup=keyboard)


@router.callback_query(F.data.startswith('admin_cat_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор категории для товара"""
    await callback.answer()
    category_id = int(callback.data.split('_')[2])

    await state.update_data(category_id=category_id)
    await state.set_state(ProductForm.title)

    try:
        await callback.message.edit_text(
            '📝 Введите название товара:\n\n'
            'Для отмены отправьте /cancel'
        )
    except Exception:
        pass


@router.callback_query(F.data == 'admin_cancel')
async def admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена добавления"""
    await callback.answer()
    await state.clear()

    try:
        await callback.message.edit_text(
            '❌ Добавление отменено',
            reply_markup=None
        )
    except Exception:
        pass


@router.message(ProductForm.title)
async def add_product_title(message: Message, state: FSMContext) -> None:
    """Получение названия товара"""
    title = message.text.strip()

    if not title:
        await message.answer('❌ Название не может быть пустым. Попробуйте ещё раз:')
        return

    await state.update_data(title=title)
    await state.set_state(ProductForm.desc)
    await message.answer(
        '📝 Введите описание товара:\n\n'
        'Для отмены отправьте /cancel'
    )


@router.message(ProductForm.desc)
async def add_product_desc(message: Message, state: FSMContext) -> None:
    """Получение описания товара"""
    desc = message.text.strip()

    if not desc:
        await message.answer('❌ Описание не может быть пустым. Попробуйте ещё раз:')
        return

    await state.update_data(desc=desc)
    await state.set_state(ProductForm.price)
    await message.answer(
        '💰 Введите цену товара (в рублях):\n\n'
        'Для отмены отправьте /cancel'
    )


@router.message(ProductForm.price)
async def add_product_price(message: Message, state: FSMContext) -> None:
    """Получение цены товара"""
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer('❌ Введите корректную цену (число больше 0):')
        return

    data = await state.get_data()
    category_id = data.get('category_id')
    title = data.get('title')
    desc = data.get('desc')

    try:
        await db.add_product(category_id, title, desc, price)
        await state.clear()
        await message.answer(
            f'✅ Товар «{title}» успешно добавлен!\n'
            f'💰 Цена: {price}₽',
            reply_markup=admin_menu()
        )
    except Exception:
        await message.answer(
            '❌ Ошибка при добавлении товара',
            reply_markup=admin_menu()
        )


@router.message(F.text == '📦 Товары')
async def show_products(message: Message) -> None:
    """Показ всех товаров"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer('⛔️ У вас нет доступа к админ-панели')
        return

    products = await db.get_products()
    if not products:
        await message.answer(
            '📦 Товаров пока нет',
            reply_markup=admin_menu()
        )
        return

    await message.answer(
        '📦 Список всех товаров:\n\n'
        'Выберите товар для управления:',
        reply_markup=products_admin_keyboard(products)
    )


@router.callback_query(F.data.startswith('admin_prod_'))
async def admin_product_card(callback: CallbackQuery) -> None:
    """Карточка товара в админке"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    product = await db.get_product_by_id(product_id)

    if not product:
        try:
            await callback.message.edit_text('❌ Товар не найден')
        except Exception:
            pass
        return

    text = (
        f"📦 <b>{product['title']}</b>\n\n"
        f"📝 {product['desc']}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>\n"
        f"🆔 ID: {product['id']}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Цена', callback_data=f'edit_price_{product_id}')],
        [InlineKeyboardButton(text='📝 Описание', callback_data=f'edit_desc_{product_id}')],
        [InlineKeyboardButton(text='🗑 Удалить', callback_data=f'delete_prod_{product_id}')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_products')]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_products')
async def back_to_products(callback: CallbackQuery) -> None:
    """Возврат к списку товаров"""
    await callback.answer()
    products = await db.get_products()

    try:
        await callback.message.edit_text(
            '📦 Список всех товаров:\n\n'
            'Выберите товар для управления:',
            reply_markup=products_admin_keyboard(products)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало редактирования цены"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditPriceForm.price)

    try:
        await callback.message.edit_text(
            '💰 Введите новую цену товара:\n\n'
            'Для отмены отправьте /cancel'
        )
    except Exception:
        pass


@router.message(EditPriceForm.price)
async def edit_price_finish(message: Message, state: FSMContext) -> None:
    """Получение новой цены"""
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer('❌ Введите корректную цену (число больше 0):')
        return

    data = await state.get_data()
    product_id = data.get('product_id')

    try:
        await db.update_product_price(product_id, price)
        await state.clear()
        await message.answer(
            f'✅ Цена товара обновлена: {price}₽',
            reply_markup=admin_menu()
        )
    except Exception:
        await message.answer(
            '❌ Ошибка при обновлении цены',
            reply_markup=admin_menu()
        )


@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало редактирования описания"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditDescForm.desc)

    try:
        await callback.message.edit_text(
            '📝 Введите новое описание товара:\n\n'
            'Для отмены отправьте /cancel'
        )
    except Exception:
        pass


@router.message(EditDescForm.desc)
async def edit_desc_finish(message: Message, state: FSMContext) -> None:
    """Получение нового описания"""
    desc = message.text.strip()

    if not desc:
        await message.answer('❌ Описание не может быть пустым. Попробуйте ещё раз:')
        return

    data = await state.get_data()
    product_id = data.get('product_id')

    try:
        await db.update_product_desc(product_id, desc)
        await state.clear()
        await message.answer(
            '✅ Описание товара обновлено!',
            reply_markup=admin_menu()
        )
    except Exception:
        await message.answer(
            '❌ Ошибка при обновлении описания',
            reply_markup=admin_menu()
        )


@router.callback_query(F.data.startswith('delete_prod_'))
async def delete_product(callback: CallbackQuery) -> None:
    """Удаление товара"""
    await callback.answer()
    product_id = int(callback.data.split('_')[2])

    try:
        await db.delete_product(product_id)
        await callback.message.edit_text(
            '✅ Товар успешно удалён!',
            reply_markup=None
        )
    except Exception:
        try:
            await callback.message.edit_text(
                '❌ Ошибка при удалении товара',
                reply_markup=None
            )
        except Exception:
            pass


@router.message(Command('cancel'))
async def cancel_command(message: Message, state: FSMContext) -> None:
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS

    await message.answer(
        '❌ Действие отменено',
        reply_markup=main_menu(is_admin=is_admin)
    )
