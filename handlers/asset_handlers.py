import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.database import SessionLocal
from keyboards import category_keyboard, interval_keyboard

router = Router()
db = SessionLocal()


# Обработчик выбора категории
@router.message(lambda message: message.text == "Просмотр активов")
async def view_assets(message: Message):
    await message.answer("Выберите категорию активов:", reply_markup=category_keyboard())


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
        url = f"https://wondrous-largely-dogfish.ngrok-free.app//current/{asset_type}/{asset}?interval={interval}"
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