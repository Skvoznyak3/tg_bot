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
    # Логика просмотра и управления подписками
    user_id = message.from_user.id
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    if subscriptions:
        reply = "Ваши активные подписки:\n" + "\n".join([s.ticker for s in subscriptions])
    else:
        reply = "У вас нет активных подписок."
    await message.reply(reply)