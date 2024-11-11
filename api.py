import httpx
from config import API_BASE_URL

async def get_assets(category, filters=None):
    async with httpx.AsyncClient() as client:
        params = {'category': category}
        if filters:
            params.update(filters)
        response = await client.get(f"{API_BASE_URL}/assets", params=params)
    return response.json()

async def get_asset_info(ticker, period='day'):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/asset/{ticker}", params={'period': period})
    return response.json()
