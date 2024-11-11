import types
import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InputFile, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from api import get_asset_info, get_chart_data
from database import SessionLocal, User, Favorite, Subscription
import matplotlib.pyplot as plt
import io

from keyboards import interval_keyboard, category_keyboard

router = Router()
db = SessionLocal()


# Главное меню
def main_menu():
    menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотр активов")],
            [KeyboardButton(text="Избранное")],
            [KeyboardButton(text="Настройки")],
            [KeyboardButton(text="Помощь")]
        ],
        resize_keyboard=True
    )
    return menu


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


# Обработчик выбора категории
@router.message(lambda message: message.text == "Просмотр активов")
async def view_assets(message: Message):
    await message.answer("Выберите категорию активов:", reply_markup=category_keyboard())

@router.callback_query(lambda c: c.data.startswith("category"))
async def process_category_callback(callback_query: CallbackQuery):
    category = callback_query.data.split(":")[1]
    base_url = "http://bigidulka2.ddns.net:8000"

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


@router.message(lambda message: message.text == "Избранное")
async def view_favorites(message: Message):
    await message.answer("Ваши избранные активы: ...")  # Добавьте логику получения избранных активов


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


@router.message(Command(commands=["info"]))
async def get_asset_info(message: Message):
    text = message.text.split()
    if len(text) < 2:
        await message.answer("Please specify the asset. Example: /info BTC")
        return

    asset_type = 'crypto'  # Default to 'crypto', or customize based on user input
    asset = text[1].upper()

    # Send a message with the inline keyboard for interval selection
    await message.answer(
        f"Choose an interval for {asset}:",
        reply_markup=interval_keyboard(asset_type, asset)
    )


@router.callback_query(lambda c: c.data.startswith("interval"))
async def process_interval_callback(callback_query: CallbackQuery):
    try:
        _, asset_type, asset, interval = callback_query.data.split(":")

        # Construct the API URL with the selected interval
        url = f"http://bigidulka2.ddns.net:8000/current/{asset_type}/{asset}?interval={interval}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract asset information safely
        asset_info = f"**{asset.upper()}** ({interval}):\n"
        asset_info += f"Price (Close): {data.get('Close', 'N/A')}\n"
        asset_info += f"Volume: {data.get('Volume', 'N/A')}\n"
        asset_info += f"Market Cap: {data.get('info', {}).get('marketCap', 'N/A')}\n"
        asset_info += f"Change: {data.get('info', {}).get('change', 'N/A')}%\n"

        await callback_query.message.answer(asset_info, parse_mode="Markdown")
        await callback_query.answer()  # Acknowledge the callback
    except Exception as e:
        await callback_query.message.answer(f"Error fetching data: {e}")
        await callback_query.answer()



@router.message(Command("chart"))
async def chart(message: Message):
    ticker = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if ticker:
        data = await get_chart_data(ticker)
        if data:
            plt.figure()
            plt.plot(data["dates"], data["prices"], label=ticker)
            plt.xlabel("Дата")
            plt.ylabel("Цена")
            plt.title(f"График {ticker}")
            plt.legend()
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            await message.reply_photo(InputFile(buf, filename="chart.png"))
            buf.close()
        else:
            await message.reply("Не удалось получить данные для графика.")
    else:
        await message.reply("Пожалуйста, укажите тикер актива после команды /chart")


@router.message(Command("subscribe"))
async def subscribe(message: Message):
    # Реализация логики подписки на уведомления об изменении цены
    ticker = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if ticker:
        new_subscription = Subscription(user_id=message.from_user.id, ticker=ticker)
        db.add(new_subscription)
        db.commit()
        await message.reply(f"Подписка на уведомления по {ticker} успешно оформлена.")
    else:
        await message.reply("Пожалуйста, укажите тикер актива после команды /subscribe")


@router.message(Command("favorites"))
async def favorites(message: Message):
    # Реализация логики управления избранными активами
    user_id = message.from_user.id
    favorites = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    if favorites:
        reply = "Ваши избранные активы:\n" + "\n".join([f.ticker for f in favorites])
    else:
        reply = "У вас нет избранных активов."
    await message.reply(reply)


@router.message(Command("settings"))
async def settings(message: Message):
    await message.reply(
        "Настройки:\n"
        "1. Базовая валюта\n"
        "2. Часовой пояс\n"
        "3. Частота уведомлений\n"
        "Для изменения параметра введите команду /set [параметр] [значение]"
    )


@router.message(Command("subscriptions"))
async def subscriptions(message: Message):
    # Логика просмотра и управления подписками
    user_id = message.from_user.id
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    if subscriptions:
        reply = "Ваши активные подписки:\n" + "\n".join([s.ticker for s in subscriptions])
    else:
        reply = "У вас нет активных подписок."
    await message.reply(reply)
