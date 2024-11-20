import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import joinedload

from database.database import SessionLocal, User, Subscription
from keyboards import main_menu, get_settings_menu
from utils import format_assets

router = Router()
db = SessionLocal()


@router.message(Command("start"))
async def send_welcome(message: Message):
    """Отправляет приветственное сообщение и отображает главное меню при вводе команды /start."""
    welcome_text = (
        "Привет! Я ваш бот для отслеживания активов.\n\n"
        "Вот что я умею:\n"
        "- Просматривать список активов (акции, валюты, криптовалюты)\n"
        "- Управлять избранными активами\n"
        "- Настраивать уведомления о цене активов\n"
        "- Показывать справочную информацию\n\n"
        "Выберите нужную опцию в меню ниже!"
    )
    await message.answer(welcome_text, reply_markup=main_menu())


@router.callback_query(lambda c: c.data.startswith("category"))
async def process_category_callback(callback_query: CallbackQuery):
    category = callback_query.data.split(":")[1]
    base_url = "https://wondrous-largely-dogfish.ngrok-free.app/"

    # Определяем конечный URL на основе выбранной категории
    if category == "stocks":
        url = f"{base_url}/stocks"
    elif category == "cryptocurrencies":
        url = f"{base_url}/cryptocurrencies"
    elif category == "currencies":
        url = f"{base_url}/currency_crosses"
    else:
        await callback_query.message.answer("Неверная категория.")
        return

    try:
        response = requests.get(url)
        response.raise_for_status()
        assets = response.json()

        message_text = format_assets(assets, category)
        await callback_query.message.answer(message_text)
        await callback_query.answer()  # Подтверждение callback-запроса

    except requests.RequestException as e:
        await callback_query.message.answer(f"Ошибка при получении данных: {e}")
        await callback_query.answer()


@router.message(lambda message: message.text == "Настройки")
@router.message(Command("settings"))
async def settings_command(message: Message):
    """
    Обработчик команды /settings. Показывает меню настроек.
    """
    await message.answer("Выберите параметр для изменения:", reply_markup=get_settings_menu())


@router.callback_query(lambda c: c.data.startswith("settings:currency"))
async def change_currency(callback_query: CallbackQuery):
    """
    Обработчик для изменения базовой валюты.
    """
    currencies = ["USD", "EUR", "RUB", "JPY"]  # Список поддерживаемых валют
    currency_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=currency, callback_data=f"set_currency:{currency}") for currency in currencies]
    ])
    await callback_query.message.answer("Выберите базовую валюту:", reply_markup=currency_menu)
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("set_currency:"))
async def set_currency(callback_query: CallbackQuery):
    """
    Устанавливает базовую валюту для пользователя.
    """
    currency = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    # Обновление валюты в базе данных
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.currency = currency
        db.commit()
        await callback_query.message.answer(f"Базовая валюта изменена на {currency}.")
    else:
        await callback_query.message.answer("Пользователь не найден. Попробуйте снова.")

    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("settings:timezone"))
async def change_timezone(callback_query: CallbackQuery):
    """
    Обработчик для изменения часового пояса.
    """
    await callback_query.message.answer("Введите ваш часовой пояс (например, UTC+3):")
    await callback_query.answer()


@router.message(lambda message: message.text.startswith("UTC"))
async def set_timezone(message: Message):
    """
    Устанавливает часовой пояс для пользователя.
    """
    timezone = message.text.strip()
    user_id = message.from_user.id

    # Обновление часового пояса в базе данных
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.timezone = timezone
        db.commit()
        await message.answer(f"Ваш часовой пояс изменен на {timezone}.")
    else:
        await message.answer("Пользователь не найден. Попробуйте снова.")


@router.callback_query(lambda c: c.data.startswith("settings:notifications"))
async def change_notifications(callback_query: CallbackQuery):
    """
    Обработчик для изменения частоты уведомлений.
    """
    notification_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Каждый час", callback_data="set_notifications:60")],
        [InlineKeyboardButton(text="Каждые 6 часов", callback_data="set_notifications:360")],
        [InlineKeyboardButton(text="Каждые 12 часов", callback_data="set_notifications:720")],
        [InlineKeyboardButton(text="Ежедневно", callback_data="set_notifications:1440")]
    ])
    await callback_query.message.answer("Выберите частоту уведомлений:", reply_markup=notification_menu)
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("set_notifications:"))
async def set_notifications(callback_query: CallbackQuery):
    """
    Устанавливает частоту уведомлений для пользователя.
    """
    frequency = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    # Обновление частоты уведомлений в базе данных
    user = db.query(User).filter(User.telegram_id == user_id).options(joinedload(User.subscriptions)).first()
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if user:
        if subscriptions:
            subscriptions.period = frequency
            db.commit()
            await callback_query.message.answer(f"Частота уведомлений изменена на каждые {frequency // 60} часов.")
        else:
            # Логика на случай, если подписки отсутствуют
            await callback_query.message.answer("У вас нет активных подписок.")
    else:
        await callback_query.message.answer("Пользователь не найден. Попробуйте снова.")

    await callback_query.answer()


@router.message(lambda message: message.text == "Помощь")
async def help(message: Message):
    help_text = (
        "Команды:\n"
        "/start - Начать работу и показать меню\n"
        "/info [тикер] - Получить информацию об активе\n"
        "/chart [тикер] - Показать график изменения цены\n"
        "/subscribe [тикер] - Настроить уведомления о цене\n"
        "/alert [тикер] - Настроить уведомление по достижении цены\n"
        "/favorites - Управление избранными активами\n"
        "/settings - Изменить настройки\n"
        "/help - Показать справку\n"
        "/subscriptions - Управление подписками\n"
    )
    await message.answer(help_text)


@router.message(Command("help"))
async def help_command(message: Message):
    await message.reply(
        "/start — Приветствие\n"
        "/info [тикер] — Получение информации об активе\n"
        "/chart [тикер] — График изменения цены\n"
        "/subscribe [тикер] — Подписка на уведомления об изменении цены\n"
        "/alert [тикер] — Настройка уведомлений по цене\n"
        "/favorites — Управление избранными активами\n"
        "/settings — Настройки бота\n"
        "/subscriptions — Управление подписками\n"
    )
