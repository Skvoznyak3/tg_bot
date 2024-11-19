import httpx

from config import BASE_API_URL


# Словарь URL-ов по типу актива
URLS = {
    "crypto": f"http://{BASE_API_URL}/current/crypto/",
    "stock": f"http://{BASE_API_URL}/current/stock/",
    "currency": f"http://{BASE_API_URL}/current/currency/"
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
