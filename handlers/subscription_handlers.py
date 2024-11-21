from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.database import Subscription, SessionLocal
from utils import parse_notification_request

router = Router()
db = SessionLocal()

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


@router.message(Command("subscriptions"))
async def subscriptions(message: Message):
    user_id = message.from_user.id
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    if subscriptions:
        reply = "Ваши активные подписки:\n"
        for sub in subscriptions:
            if sub.type == "price_level":
                reply += f"Актив: {sub.ticker}, Уровень цены: {sub.threshold}\n"
            else:
                reply += f"Актив: {sub.ticker}, Тип: {sub.type}, Порог: {sub.threshold}\n"
    else:
        reply = "У вас нет активных подписок."
    await message.reply(reply)



@router.message(Command("alert"))
async def alert(message: Message):
    """
    Настройка уведомления при достижении определенной цены актива.
    Пример использования: /alert BTC 50000
    """
    try:
        # Разбираем команду
        command_parts = message.text.split()
        if len(command_parts) != 3:
            await message.reply("Введите команду в формате: /alert [тикер] [цена]. Пример: /alert BTC 50000")
            return

        ticker = command_parts[1].upper()  # Пример: BTC
        price_level = float(command_parts[2])  # Пример: 50000

        # Сохраняем подписку в базу данных
        new_subscription = Subscription(
            user_id=message.from_user.id,
            ticker=ticker,
            type="price_level",
            threshold=price_level,
        )
        db.add(new_subscription)
        db.commit()

        await message.reply(f"Уведомление при достижении цены {price_level} для актива {ticker} успешно настроено.")
    except ValueError:
        await message.reply("Указана некорректная цена. Пожалуйста, введите команду в формате: /alert [тикер] [цена].")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")
