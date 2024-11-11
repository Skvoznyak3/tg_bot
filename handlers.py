import types
from sqlite3 import IntegrityError

import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InputFile, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from api import get_asset_info, get_chart_data, get_unknown_asset_info
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
async def list_favorites(message: Message):
    """Отправка пользователю списка избранных активов."""
    user_id = message.from_user.id
    response = await get_favorites(user_id)
    await message.answer(response)


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


async def parse_notification_request(text: str):
    parts = text.split()
    if len(parts) != 3:
        return None, None, None
    ticker, notification_type, threshold = parts
    if notification_type == "процент":
        try:
            threshold = float(threshold)
            return ticker, "percent", threshold
        except ValueError:
            return None, None, None
    elif notification_type == "цена":
        try:
            threshold = float(threshold)
            return ticker, "price", threshold
        except ValueError:
            return None, None, None
    return None, None, None


@router.message(Command("subscribe"))
async def subscribe(message: Message):
    # Реализация логики подписки на уведомления об изменении цены
    ticker, notification_type, threshold = await parse_notification_request(message.text)
    if ticker and notification_type and threshold:
        new_subscription = Subscription(user_id=message.from_user.id, ticker=ticker, type=notification_type,
                                        threshold=threshold)
        db.add(new_subscription)
        db.commit()
        await message.reply(f"Подписка на уведомления по {ticker} успешно оформлена.")
    else:
        await message.reply("Введите тикер актива, тип уведомления (в процентах) и параметры "
                            "уведомления.\n"
                            "Пример: `BTC процент 5`")


# Хендлер для команды /subscriptions
@router.message(Command("subscriptions"))
async def view_subscriptions(message: Message):
    user_id = message.from_user.id
    session = SessionLocal()

    # Получаем список подписок пользователя
    subscriptions = session.query(Subscription).filter_by(user_id=user_id).all()

    if not subscriptions:
        await message.answer("У вас нет активных подписок.")
    else:
        response = "Ваши активные подписки:\n"
        for subscription in subscriptions:
            if subscription.alert_type == 'percentage':
                response += f"Актив: {subscription.ticker}, Уведомление при изменении на {subscription.alert_value}%\n"
            elif subscription.alert_type == 'price_level':
                response += f"Актив: {subscription.ticker}, Уведомление при достижении цены {subscription.alert_value}\n"
        response += "\nЧтобы удалить подписку, введите /unsubscribe <тикер>."

        await message.answer(response)

    session.close()

async def add_to_favorites(user_id, ticker):
    """Добавление актива в избранное."""
    session = SessionLocal()
    # Пример использования
    asset_info = await get_unknown_asset_info(ticker, "1d")
    if isinstance(asset_info, str):
        # Обработка ошибки, если актив не найден
        print(asset_info)
        session.close()
        return f"Актив {ticker} не найден."
    else:
        # Обработка успешного ответа, asset_info содержит тип актива и данные
        asset_type = asset_info["type"]
        data = asset_info["data"]
        print(f"Тип актива: {asset_type}, Данные: {data}")
        try:
            favorite = Favorite(user_id=user_id, ticker=ticker)
            session.add(favorite)
            session.commit()
            return f"Актив {ticker} добавлен в избранное."
        except IntegrityError:
            session.rollback()
            return f"Актив {ticker} уже в избранном."
        finally:
            session.close()


async def remove_from_favorites(user_id, ticker):
    """Удаление актива из избранного."""
    session = SessionLocal()
    favorite = session.query(Favorite).filter_by(user_id=user_id, ticker=ticker).first()
    if favorite:
        session.delete(favorite)
        session.commit()
        message = f"Актив {ticker} удален из избранного."
    else:
        message = f"Актив {ticker} не найден в избранном."
    session.close()
    return message


async def get_favorites(user_id):
    """Получение списка избранных активов пользователя."""
    session = SessionLocal()
    favorites = session.query(Favorite).filter_by(user_id=user_id).all()
    session.close()
    if favorites:
        return "Ваши избранные активы:\n" + "\n".join([f.ticker for f in favorites])
    return "Ваш список избранных пуст."


@router.message(Command("favorite"))
async def handle_favorite_command(message: Message):
    """Обработка команды избранного, добавление или удаление актива."""
    user_id = message.from_user.id
    command_parts = message.text.split()

    if len(command_parts) < 3:
        await message.answer("Используйте формат: /favorite <добавить/удалить> <тикер>")
        return

    action, ticker = command_parts[1], command_parts[2].upper()

    if action == "добавить":
        response = await add_to_favorites(user_id, ticker)
    elif action == "удалить":
        response = await remove_from_favorites(user_id, ticker)
    else:
        response = "Неизвестное действие. Используйте 'добавить' или 'удалить'."

    await message.answer(response)


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
