from aiogram import types
from api import get_assets, get_asset_info
from database import SessionLocal, User
from aiogram.dispatcher import Dispatcher

db = SessionLocal()

async def start(message: types.Message):
    user_id = message.from_user.id
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        new_user = User(telegram_id=user_id)
        db.add(new_user)
        db.commit()
    await message.reply("Добро пожаловать! Используйте /help для списка команд.")

async def info(message: types.Message):
    ticker = message.get_args()
    if ticker:
        data = await get_asset_info(ticker)
        if data:
            reply = f"{data['name']} ({data['ticker']}): Цена {data['price']}, Объем {data['volume']}"
        else:
            reply = "Актив не найден."
        await message.reply(reply)

async def favorites(message: types.Message):
    user_id = message.from_user.id
    favs = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    if favs:
        favs_list = "\n".join([fav.ticker for fav in favs])
        await message.reply(f"Ваши избранные активы:\n{favs_list}")
    else:
        await message.reply("Список избранных пуст.")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands=["start"])
    dp.register_message_handler(info, commands=["info"])
    dp.register_message_handler(favorites, commands=["favorites"])
