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