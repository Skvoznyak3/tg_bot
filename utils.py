async def parse_notification_request(text: str):
    parts = text.split()
    if len(parts) != 3:
        return None, None, None
    ticker, notification_type, threshold = parts
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
