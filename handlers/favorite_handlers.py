from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.crud import get_favorites, add_to_favorites, remove_from_favorites
from database.database import SessionLocal

router = Router()
db = SessionLocal()


@router.message(lambda message: message.text == "Избранное")
async def list_favorites(message: Message):
    """Отправка пользователю списка избранных активов."""
    user_id = message.from_user.id
    response = await get_favorites(user_id)
    await message.answer(response)


@router.message(Command("favorite"))
async def handle_favorite_command(message: Message):
    """Обработка команды избранного, добавление или удаление актива."""
    user_id = message.from_user.id
    command_parts = message.text.split()

    if len(command_parts) < 3:
        await message.answer("Используйте формат: /favorite <добавить/удалить> <тикер>")
        return

    action, ticker = command_parts[1], command_parts[2].upper()

    if action == "добавить":
        response = await add_to_favorites(user_id, ticker)
    elif action == "удалить":
        response = await remove_from_favorites(user_id, ticker)
    else:
        response = "Неизвестное действие. Используйте 'добавить' или 'удалить'."

    await message.answer(response)

