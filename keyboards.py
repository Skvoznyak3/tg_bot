from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


# Function to generate inline keyboard with interval options
def interval_keyboard(asset_type, asset):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 Hour", callback_data=f"interval:{asset_type}:{asset}:1h"),
            InlineKeyboardButton(text="1 Day", callback_data=f"interval:{asset_type}:{asset}:1d"),
            InlineKeyboardButton(text="1 Week", callback_data=f"interval:{asset_type}:{asset}:1wk")
        ]
    ])
    return keyboard


def category_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Акции", callback_data="category:stocks")],
        [InlineKeyboardButton(text="Криптовалюты", callback_data="category:cryptocurrencies")],
        [InlineKeyboardButton(text="Валюты", callback_data="category:currencies")]
    ])
    return keyboard


# Главное меню
def main_menu():
    menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотр активов")],
            [KeyboardButton(text="Избранное")],
            [KeyboardButton(text="Настройки", callback_data="settings")],
            [KeyboardButton(text="Помощь")]
        ],
        resize_keyboard=True
    )
    return menu


def get_settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить базовую валюту", callback_data="settings:currency")],
        [InlineKeyboardButton(text="Изменить часовой пояс", callback_data="settings:timezone")],
        [InlineKeyboardButton(text="Изменить частоту уведомлений", callback_data="settings:notifications")],
    ])