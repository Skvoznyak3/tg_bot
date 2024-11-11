from aiogram import Bot, Dispatcher, executor
from config import API_TOKEN
from handlers import register_handlers

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

register_handlers(dp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
