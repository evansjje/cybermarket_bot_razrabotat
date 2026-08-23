# handlers/other.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database import get_user, add_referral, get_referrals_count, get_reviews, add_review
from keyboards import referrals_kb, reviews_kb, support_kb

router = Router()


@router.message(F.text == "👥 Рефералка")
async def show_referral(message: Message) -> None:
    """Показать реферальную информацию"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user:
        await message.answer("❌ Пользователь не найден. Нажмите /start")
        return

    # Генерируем реферальную ссылку
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    referrals_count = await get_referrals_count(user_id)

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Приглашено друзей: <b>{referrals_count}</b>\n\n"
        f"💰 За каждого приглашенного друга вы получаете бонусы!\n"
        f"Поделитесь ссылкой и получайте вознаграждения."
    )

    await message.answer(text, reply_markup=referrals_kb())


@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message) -> None:
    """Показать отзывы"""
    reviews = await get_reviews()

    if not reviews:
        text = (
            f"⭐ <b>Отзывы</b>\n\n"
            f"Пока нет отзывов. Будьте первым!"
        )
    else:
        text = "⭐ <b>Отзывы наших клиентов</b>\n\n"
        for review in reviews:
            # review: (id, user_id, username, text, rating, created_at)
            username = review[2] or "Пользователь"
            review_text = review[3]
            rating = review[4]
            stars = "⭐" * rating
            text += f"{stars} <b>{username}</b>:\n{review_text}\n\n"

    await message.answer(text, reply_markup=reviews_kb())


@router.message(F.text == "🆘 Поддержка")
async def show_support(message: Message) -> None:
    """Показать информацию о поддержке"""
    text = (
        f"🆘 <b>Поддержка</b>\n\n"
        f"Если у вас возникли вопросы или проблемы, мы всегда готовы помочь!\n\n"
        f"📧 Напишите нам на email: support@cybermarket.com\n"
        f"💬 Или свяжитесь с нами в Telegram: @CyberMarketSupport\n\n"
        f"⏰ Время работы: 24/7\n"
        f"⚡ Среднее время ответа: до 15 минут"
    )

    await message.answer(text, reply_markup=support_kb())


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    """Вернуться в главное меню"""
    from keyboards import main_menu_kb
    user_id = callback.from_user.id

    await callback.message.answer(
        "Вы вернулись в главное меню:",
        reply_markup=main_menu_kb(user_id)
    )
    await callback.answer()


@router.callback_query(F.data == "share_referral")
async def share_referral(callback: CallbackQuery) -> None:
    """Поделиться реферальной ссылкой"""
    user_id = callback.from_user.id
    bot_username = (await callback.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    await callback.message.answer(
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        f"Скопируйте и отправьте друзьям!"
    )
    await callback.answer()


@router.callback_query(F.data == "write_review")
async def write_review(callback: CallbackQuery) -> None:
    """Начать написание отзыва"""
    await callback.message.answer(
        "📝 Напишите ваш отзыв в следующем сообщении.\n"
        "Формат: <code>отзыв|оценка</code>\n"
        "Оценка от 1 до 5 (например: отзыв|5)"
    )
    await callback.answer()


@router.message(F.text.contains("|"))
async def process_review(message: Message) -> None:
    """Обработка отзыва"""
    try:
        parts = message.text.split("|")
        if len(parts) != 2:
            await message.answer("❌ Неверный формат. Используйте: <code>отзыв|оценка</code>")
            return

        review_text = parts[0].strip()
        rating = int(parts[1].strip())

        if rating < 1 or rating > 5:
            await message.answer("❌ Оценка должна быть от 1 до 5")
            return

        if not review_text:
            await message.answer("❌ Текст отзыва не может быть пустым")
            return

        user_id = message.from_user.id
        username = message.from_user.username or "Пользователь"

        await add_review(
            user_id=user_id,
            username=username,
            text=review_text,
            rating=rating
        )

        stars = "⭐" * rating
        await message.answer(
            f"✅ Спасибо за ваш отзыв!\n\n"
            f"{stars} <b>{username}</b>:\n{review_text}"
        )

    except ValueError:
        await message.answer("❌ Оценка должна быть числом от 1 до 5")
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении отзыва: {e}")


@router.callback_query(F.data.startswith("ref_"))
async def process_referral(callback: CallbackQuery) -> None:
    """Обработка реферальной ссылки"""
    try:
        referrer_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id

        if referrer_id == user_id:
            await callback.answer("❌ Нельзя пригласить самого себя!")
            return

        # Проверяем, не был ли пользователь уже приглашен
        user = await get_user(user_id)
        if user and user[5]:  # если есть referral_id
            await callback.answer("❌ Вы уже были приглашены ранее!")
            return

        # Добавляем реферальную связь
        await add_referral(user_id=user_id, referrer_id=referrer_id)

        await callback.answer("✅ Вы успешно активировали реферальную ссылку!")
        await callback.message.answer(
            "🎉 Реферальная ссылка активирована!\n"
            "Вы получили бонус на счет!"
        )

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}")
