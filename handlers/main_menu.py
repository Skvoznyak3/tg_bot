import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.database import SessionLocal
from keyboards import main_menu

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

        # Вывод краткой информации по активам
        message_text = "Список активов:\n"
        for asset in assets[:10]:  # ограничим вывод до 10 активов
            name = asset.get("name", "N/A")
            if category == "stocks":
                symbol = asset.get("symbol", "N/A")
                isin = asset.get("isin", "N/A")
                currency = asset.get("currency") if "currency" in asset else "Данные отсутствуют"

                message_text += (
                    f"{name} ({symbol}):\n"
                    f"ISIN: {isin}\n"
                    f"Валюта: {currency}\n"
                )
            elif category == "cryptocurrencies":
                symbol = asset.get("symbol", "N/A")
                currency = asset.get("currency") if "currency" in asset else "Данные отсутствуют"

                message_text += (
                    f"{name} ({symbol}):\n"
                    f"Валюта: {currency}\n"
                )
            elif category == "currencies":
                base = asset.get("base")
                base_name = asset.get("base_name")
                second = asset.get("second")
                second_name = asset.get("second_name")

                message_text += (
                    f"{name}:\n"
                    f"Основная валюта: {base_name} ({base})\n"
                    f"Вторая валюта: {second_name} ({second})\n"
                )

            message_text += "\n"

        await callback_query.message.answer(message_text)
        await callback_query.answer()  # Подтверждение callback-запроса

    except requests.RequestException as e:
        await callback_query.message.answer(f"Ошибка при получении данных: {e}")
        await callback_query.answer()


@router.message(lambda message: message.text == "Настройки")
async def settings(message: Message):
    await message.answer(
        "Здесь вы можете изменить настройки, такие как часовой пояс, базовая валюта и частота уведомлений.")


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