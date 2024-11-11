from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Function to generate inline keyboard with interval options
def interval_keyboard(asset_type, asset):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 Hour", callback_data=f"interval:{asset_type}:{asset}:1h"),
            InlineKeyboardButton(text="1 Day", callback_data=f"interval:{asset_type}:{asset}:1d"),
            InlineKeyboardButton(text="1 Week", callback_data=f"interval:{asset_type}:{asset}:1w")
        ]
    ])
    return keyboard
