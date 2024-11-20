async def parse_notification_request(text: str):
    parts = text.split()
    if len(parts) != 4:
        return None, None, None
    _, ticker, notification_type, threshold = parts
    if notification_type == "процент":
        try:
            threshold = float(threshold)
            return ticker, "percent", threshold
        except ValueError:
            return None, None, None
    elif notification_type == "цена":
        try:
            threshold = float(threshold)
            return ticker, "price", threshold
        except ValueError:
            return None, None, None
    return None, None, None


def format_assets(assets, category):
    message_text = "Список активов:\n"
    for asset in assets[:10]:  # ограничим вывод до 10 активов
        if category == "stocks":
            name, symbol, isin, currency = (
                asset.get("name", "N/A"),
                asset.get("symbol", "N/A"),
                asset.get("isin", "N/A"),
                asset.get("currency", "N/A")
            )
            message_text += f"{name} ({symbol}):\nISIN: {isin}\nВалюта: {currency}\n\n"
        elif category == "cryptocurrencies":
            name, symbol, currency = (
                asset.get("name", "N/A"),
                asset.get("symbol", "N/A"),
                asset.get("currency", "N/A")
            )
            message_text += f"{name} ({symbol}):\nВалюта: {currency}\n\n"
        elif category == "currencies":
            base, base_name, second, second_name = (
                asset.get("base"), asset.get("base_name"),
                asset.get("second"), asset.get("second_name")
            )
            message_text += (
                f"{asset.get('name')}:\n"
                f"Основная валюта: {base_name} ({base})\n"
                f"Вторая валюта: {second_name} ({second})\n\n"
            )
    return message_text
