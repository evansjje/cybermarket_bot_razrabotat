from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import main_menu_kb, admin_menu_kb, admin_products_kb, admin_product_actions_kb, admin_categories_kb
from config import settings

router = Router()
db = Database()


class AdminStates(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()
    waiting_for_product_file = State()
    waiting_for_edit_product_name = State()
    waiting_for_edit_product_description = State()
    waiting_for_edit_product_price = State()
    waiting_for_edit_product_category = State()
    waiting_for_edit_product_file = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(F.text == "🔐 Админ-панель")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Доступ запрещен")
        return
    await message.answer("🔐 Админ-панель", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    await callback.message.edit_text("🔐 Админ-панель", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    await callback.message.edit_text("Введите название товара:")
    await state.set_state(AdminStates.waiting_for_product_name)
    await callback.answer()


@router.message(AdminStates.waiting_for_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await state.set_state(AdminStates.waiting_for_product_description)


@router.message(AdminStates.waiting_for_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену товара (в рублях):")
    await state.set_state(AdminStates.waiting_for_product_price)


@router.message(AdminStates.waiting_for_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
        await state.update_data(price=price)
        await message.answer("Выберите категорию:", reply_markup=admin_categories_kb())
        await state.set_state(AdminStates.waiting_for_product_category)
    except ValueError:
        await message.answer("❌ Введите корректную цену (положительное число)")


@router.callback_query(AdminStates.waiting_for_product_category)
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_", 1)[1]
    await state.update_data(category=category)
    await callback.message.edit_text("Отправьте файл товара (или ссылку на него):")
    await state.set_state(AdminStates.waiting_for_product_file)
    await callback.answer()


@router.message(AdminStates.waiting_for_product_file)
async def admin_add_product_file(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = None
    file_url = None

    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.startswith("http"):
        file_url = message.text
    else:
        await message.answer("❌ Отправьте файл или ссылку на файл")
        return

    await db.add_product(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        category=data["category"],
        file_id=file_id,
        file_url=file_url
    )
    await state.clear()
    await message.answer("✅ Товар успешно добавлен!", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_list_products")
async def admin_list_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    products = await db.get_all_products()
    if not products:
        await callback.message.edit_text("📦 Товаров пока нет", reply_markup=admin_menu_kb())
    else:
        await callback.message.edit_text("📦 Список товаров:", reply_markup=admin_products_kb(products))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_"))
async def admin_edit_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[2])
    product = await db.get_product(product_id)
    if product:
        await callback.message.edit_text(
            f"📦 {product[1]}\n\n{product[2]}\n\n💰 Цена: {product[3]} руб.\n📂 Категория: {product[4]}",
            reply_markup=admin_product_actions_kb(product_id)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[2])
    await db.delete_product(product_id)
    await callback.message.edit_text("✅ Товар удален", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_name_"))
async def admin_edit_product_name(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)
    await callback.message.edit_text("Введите новое название товара:")
    await state.set_state(AdminStates.waiting_for_edit_product_name)
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_product_name)
async def admin_edit_product_name_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_product_name(data["product_id"], message.text)
    await state.clear()
    await message.answer("✅ Название обновлено!", reply_markup=admin_menu_kb())


@router.callback_query(F.data.startswith("admin_edit_desc_"))
async def admin_edit_product_desc(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)
    await callback.message.edit_text("Введите новое описание товара:")
    await state.set_state(AdminStates.waiting_for_edit_product_description)
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_product_description)
async def admin_edit_product_desc_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_product_description(data["product_id"], message.text)
    await state.clear()
    await message.answer("✅ Описание обновлено!", reply_markup=admin_menu_kb())


@router.callback_query(F.data.startswith("admin_edit_price_"))
async def admin_edit_product_price(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)
    await callback.message.edit_text("Введите новую цену товара:")
    await state.set_state(AdminStates.waiting_for_edit_product_price)
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_product_price)
async def admin_edit_product_price_handler(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
        data = await state.get_data()
        await db.update_product_price(data["product_id"], price)
        await state.clear()
        await message.answer("✅ Цена обновлена!", reply_markup=admin_menu_kb())
    except ValueError:
        await message.answer("❌ Введите корректную цену")


@router.callback_query(F.data.startswith("admin_edit_cat_"))
async def admin_edit_product_cat(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)
    await callback.message.edit_text("Выберите новую категорию:", reply_markup=admin_categories_kb())
    await state.set_state(AdminStates.waiting_for_edit_product_category)
    await callback.answer()


@router.callback_query(AdminStates.waiting_for_edit_product_category)
async def admin_edit_product_cat_handler(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_", 1)[1]
    data = await state.get_data()
    await db.update_product_category(data["product_id"], category)
    await state.clear()
    await callback.message.edit_text("✅ Категория обновлена!", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_file_"))
async def admin_edit_product_file(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)
    await callback.message.edit_text("Отправьте новый файл товара (или ссылку):")
    await state.set_state(AdminStates.waiting_for_edit_product_file)
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_product_file)
async def admin_edit_product_file_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = None
    file_url = None

    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.startswith("http"):
        file_url = message.text
    else:
        await message.answer("❌ Отправьте файл или ссылку")
        return

    await db.update_product_file(data["product_id"], file_id, file_url)
    await state.clear()
    await message.answer("✅ Файл обновлен!", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен")
        return
    await callback.message.edit_text("🔐 Админ-панель", reply_markup=admin_menu_kb())
    await callback.answer()
