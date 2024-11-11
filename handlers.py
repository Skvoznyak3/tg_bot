from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InputFile
from aiogram.fsm.context import FSMContext
from api import get_asset_info, get_chart_data
from database import SessionLocal, User, Favorite, Subscription
import matplotlib.pyplot as plt
import io

router = Router()
db = SessionLocal()


@router.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        new_user = User(telegram_id=user_id)
        db.add(new_user)
        db.commit()
    await message.reply("Добро пожаловать! Используйте /help для списка команд.")


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


@router.message(Command("info"))
async def info(message: Message):
    ticker = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if ticker:
        data = await get_asset_info(ticker)
        if data:
            reply = f"{data['name']} ({data['ticker']}): Цена {data['price']}, Объем {data['volume']}, Капитализация {data['market_cap']}"
        else:
            reply = "Актив не найден."
        await message.reply(reply)
    else:
        await message.reply("Пожалуйста, укажите тикер актива после команды /info")


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
