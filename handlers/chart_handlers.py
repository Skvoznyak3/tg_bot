import io
from datetime import datetime

import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from matplotlib import pyplot as plt

from database.database import SessionLocal

router = Router()
db = SessionLocal()


@router.message(Command(commands=["chart"]))
async def get_chart_period(message: Message):
    text = message.text.split()
    if len(text) < 2:
        await message.answer("Укажите тикер актива. Пример: /chart BTC")
        return

    asset_type = 'crypto'  # Default to 'crypto', or customize based on user input
    asset = text[1].upper()

    try:

        # Construct the API URL with the selected interval
        url = f"https://wondrous-largely-dogfish.ngrok-free.app/historical/{asset_type}/{asset}?interval=1d"
        response = requests.get(url)
        response.raise_for_status()

        # Получаем данные за нужный интервал
        all_data = response.json()
        data = all_data[-8:-1:]

        dates = [datetime.strptime(entry["Date"], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d") for entry in data]
        closes = [entry["Close_BTC-USD"] for entry in data]
        volumes = [entry["Volume_BTC-USD"] for entry in data]

        # Построение графика
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Линия закрытия цен
        ax1.plot(dates, closes, label="Цена закрытия (USD)", color='blue')
        ax1.set_xlabel("Дата")
        ax1.set_ylabel("Цена закрытия (USD)", color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1.set_xticklabels(dates, rotation=45, ha='right')

        # Столбцы объема
        ax2 = ax1.twinx()
        ax2.bar(dates, volumes, color='gray', alpha=0.3, label="Объем")
        ax2.set_ylabel("Объем", color='gray')
        ax2.tick_params(axis='y', labelcolor='gray')

        # Заголовок и легенды
        plt.title(f"График цены и объема {asset}")
        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")

        # Сохранение графика в буфер
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close(fig)

        # Отправка графика в чат
        await message.reply_photo(
            photo=BufferedInputFile(buffer.read(), filename="chart.png"),
            caption=f"График цены и объема {asset}"
        )

        # Закрытие буфера
        buffer.close()

    except Exception as e:
        await message.answer(f"Ошибка: {e}")