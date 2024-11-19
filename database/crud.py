from sqlite3 import IntegrityError

from api import get_unknown_asset_info
from database.database import SessionLocal, Favorite


async def get_favorites(user_id):
    """Получение списка избранных активов пользователя."""
    session = SessionLocal()
    favorites = session.query(Favorite).filter_by(user_id=user_id).all()
    session.close()
    if favorites:
        return "Ваши избранные активы:\n" + "\n".join([f.ticker for f in favorites])
    return "Ваш список избранных пуст."


async def add_to_favorites(user_id, ticker):
    """Добавление актива в избранное."""
    session = SessionLocal()
    # Пример использования
    asset_info = await get_unknown_asset_info(ticker, "1d")
    if isinstance(asset_info, str):
        # Обработка ошибки, если актив не найден
        print(asset_info)
        session.close()
        return f"Актив {ticker} не найден."
    else:
        # Обработка успешного ответа, asset_info содержит тип актива и данные
        asset_type = asset_info["type"]
        data = asset_info["data"]
        print(f"Тип актива: {asset_type}, Данные: {data}")
        try:
            favorite = Favorite(user_id=user_id, ticker=ticker)
            session.add(favorite)
            session.commit()
            return f"Актив {ticker} добавлен в избранное."
        except IntegrityError:
            session.rollback()
            return f"Актив {ticker} уже в избранном."
        finally:
            session.close()


async def remove_from_favorites(user_id, ticker):
    """Удаление актива из избранного."""
    session = SessionLocal()
    favorite = session.query(Favorite).filter_by(user_id=user_id, ticker=ticker).first()
    if favorite:
        session.delete(favorite)
        session.commit()
        message = f"Актив {ticker} удален из избранного."
    else:
        message = f"Актив {ticker} не найден в избранном."
    session.close()
    return message
