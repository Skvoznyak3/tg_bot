import requests
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
