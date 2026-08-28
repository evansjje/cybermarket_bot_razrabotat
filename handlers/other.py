# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from database import Database
from keyboards import get_main_menu

router = Router()


@router.message(F.text == '👥 Рефералка')
async def referral_handler(message: Message, db: Database):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    # Генерируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Получаем количество приглашенных пользователей
    invited_count = 0
    try:
        cursor = await db.db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            invited_count = row[0]
    except Exception:
        pass
    
    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        f"Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено друзей: <b>{invited_count}</b>\n\n"
        "Поделитесь этой ссылкой с друзьями и получайте бонусы за каждого приглашенного!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Скопировать ссылку",
                    callback_data="copy_referral"
                )
            ]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'copy_referral')
async def copy_referral_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    bot_username = (await callback.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await callback.message.answer(
        f"📋 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        "Скопируйте и отправьте её друзьям!"
    )


@router.message(F.text == '⭐ Отзывы')
async def reviews_handler(message: Message, db: Database):
    user_id = message.from_user.id
    
    # Получаем отзывы из БД (если таблица существует)
    reviews = []
    try:
        cursor = await db.db.execute(
            "SELECT * FROM reviews ORDER BY created_at DESC LIMIT 5"
        )
        reviews = await cursor.fetchall()
    except Exception:
        pass
    
    text = "⭐ <b>Отзывы наших клиентов</b>\n\n"
    
    if reviews:
        for review in reviews:
            user_name = review.get('user_name', 'Пользователь')
            rating = review.get('rating', 5)
            comment = review.get('comment', '')
            stars = "⭐" * rating
            text += f"<b>{user_name}</b> {stars}\n{comment}\n\n"
    else:
        text += "Пока нет отзывов. Будьте первым!\n\n"
    
    text += "Хотите оставить отзыв? Напишите нам в поддержку!"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Оставить отзыв",
                    callback_data="write_review"
                )
            ]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'write_review')
async def write_review_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📝 <b>Оставить отзыв</b>\n\n"
        "Напишите ваш отзыв в формате:\n"
        "<code>Оценка (1-5) | Ваш комментарий</code>\n\n"
        "Пример: <code>5 | Отличный магазин, быстрая доставка!</code>"
    )


@router.message(F.text.regexp(r'^[1-5]\s*\|.*'))
async def process_review(message: Message, db: Database):
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"
    first_name = message.from_user.first_name or "Пользователь"
    
    try:
        # Парсим отзыв
        parts = message.text.split('|', 1)
        rating = int(parts[0].strip())
        comment = parts[1].strip() if len(parts) > 1 else ""
        
        # Создаем таблицу отзывов, если её нет
        await db.db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Сохраняем отзыв
        await db.db.execute(
            "INSERT INTO reviews (user_id, user_name, rating, comment) VALUES (?, ?, ?, ?)",
            (user_id, first_name, rating, comment)
        )
        await db.db.commit()
        
        await message.answer(
            "✅ <b>Спасибо за ваш отзыв!</b>\n\n"
            f"Оценка: {'⭐' * rating}\n"
            f"Комментарий: {comment}\n\n"
            "Ваш отзыв будет опубликован после модерации."
        )
    except Exception as e:
        await message.answer(
            "❌ Не удалось сохранить отзыв. Попробуйте ещё раз."
        )


@router.message(F.text == '🆘 Поддержка')
async def support_handler(message: Message, db: Database):
    user_id = message.from_user.id
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, вы можете:\n\n"
        "1️⃣ Написать нам в Telegram\n"
        "2️⃣ Оставить заявку через бота\n"
        "3️⃣ Посмотреть FAQ\n\n"
        "Мы отвечаем в течение 24 часов!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📨 Написать в поддержку",
                    url="https://t.me/support"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ FAQ",
                    callback_data="faq"
                )
            ]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == 'faq')
async def faq_callback(callback: CallbackQuery):
    await callback.answer()
    
    faq_text = (
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "1️⃣ <b>Как получить товар после оплаты?</b>\n"
        "   Товар приходит автоматически после оплаты.\n\n"
        "2️⃣ <b>Как долго обрабатывается заказ?</b>\n"
        "   Обычно мгновенно, максимум 5 минут.\n\n"
        "3️⃣ <b>Что делать, если товар не пришёл?</b>\n"
        "   Напишите в поддержку, мы решим проблему.\n\n"
        "4️⃣ <b>Как получить реферальный бонус?</b>\n"
        "   Приглашайте друзей по вашей ссылке и получайте бонусы.\n\n"
        "5️⃣ <b>Есть ли гарантия на товары?</b>\n"
        "   Да, все товары имеют гарантию качества."
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back_to_support"
                )
            ]
        ]
    )
    
    try:
        await callback.message.edit_text(faq_text, reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data == 'back_to_support')
async def back_to_support_callback(callback: CallbackQuery):
    await callback.answer()
    
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, вы можете:\n\n"
        "1️⃣ Написать нам в Telegram\n"
        "2️⃣ Оставить заявку через бота\n"
        "3️⃣ Посмотреть FAQ\n\n"
        "Мы отвечаем в течение 24 часов!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📨 Написать в поддержку",
                    url="https://t.me/support"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ FAQ",
                    callback_data="faq"
                )
            ]
        ]
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass
