from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from api import get_asset_info, get_assets
from database import SessionLocal, User

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


@router.message(Command("info"))
async def info(message: Message):
    ticker = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if ticker:
        data = await get_asset_info(ticker)
        if data:
            reply = f"{data['name']} ({data['ticker']}): Цена {data['price']}, Объем {data['volume']}"
        else:
            reply = "Актив не найден."
        await message.reply(reply)
