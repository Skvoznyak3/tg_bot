import httpx
import requests
from aiogram.client.session import aiohttp

from config import API_BASE_URL


def get_asset_info(ticker):
    """Запрашивает информацию об активе по тикеру."""
    try:
        response = requests.get(f"{API_BASE_URL}/asset/{ticker}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при запросе информации об активе: {e}")
        return None


def get_chart_data(ticker):
    """Запрашивает данные для построения графика изменения цены актива."""
    try:
        response = requests.get(f"{API_BASE_URL}/asset/{ticker}/chart")
        response.raise_for_status()
        data = response.json()

        # Пример преобразования данных в формат для графика
        dates = [point["date"] for point in data["chartData"]]
        prices = [point["price"] for point in data["chartData"]]

        return {"dates": dates, "prices": prices}
    except requests.RequestException as e:
        print(f"Ошибка при запросе данных для графика: {e}")
        return None


# Словарь URL-ов по типу актива
URLS = {
    "crypto": "http://bigidulka2.ddns.net:8000/current/crypto/",
    "stock": "http://bigidulka2.ddns.net:8000/current/stock/",
    "currency": "http://bigidulka2.ddns.net:8000/current/currency/"
}


async def get_unknown_asset_info(ticker: str, interval: str = "1d"):
    async with httpx.AsyncClient() as client:
        for asset_type, base_url in URLS.items():
            url = f"{base_url}{ticker}?interval={interval}"
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return {"type": asset_type, "data": data}
                elif response.status_code == 404:
                    continue  # Актив не найден для данного типа, попробуем следующий
            except httpx.HTTPError as e:
                print(f"Ошибка при запросе к {url}: {e}")
                continue

    # Если ни один из запросов не успешен
    return f"Актив {ticker} не найден среди доступных типов: crypto, stock, currency."
