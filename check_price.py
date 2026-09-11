import json
import os
import re
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TARGET_URL = "https://www.wellcome.com.hk/zh-hant/p/%E5%8E%9F%E7%AE%B1%E9%88%A3%E6%80%9D%E5%AF%B6%E9%AB%98%E9%88%A3%20%E6%A4%8D%E7%89%A9%E5%9B%BA%E9%86%87%2024%20X%20250ML/i/113465289.html"


def fetch_current_price():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
    }
    res = requests.get(TARGET_URL, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if data.get("@type") == "Product" or "offers" in data:
                raw_price = data.get("offers", {}).get("price")
                if raw_price:
                    return {
                        "name": data.get("name", "原箱鈣思寶高鈣 植物固醇"),
                        "price": float(raw_price),
                    }
        except Exception:
            continue

    prices = re.findall(r"\$\s*(\d+(?:\.\d{1,2})?)", soup.get_text())
    valid_prices = [float(p) for p in prices if float(p) > 20]
    if valid_prices:
        return {"name": "原箱鈣思寶高鈣 植物固醇 24 X 250ML", "price": valid_prices[0]}

    raise ValueError("Could not extract price from Wellcome.")


def send_telegram_alert(message):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError(
            f"Missing Secrets! BOT_TOKEN={'SET' if BOT_TOKEN else 'EMPTY'}, "
            f"CHAT_ID={'SET' if CHAT_ID else 'EMPTY'}"
        )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    response = requests.post(url, json=payload, timeout=10)
    print(f"Telegram API Response: status={response.status_code}, body={response.text}")
    response.raise_for_status()


def main():
    item = fetch_current_price()
    msg = (
        f"🛒 *{item['name']}*\n"
        f"💰 Current Price: *${item['price']:.2f}*\n\n"
        f"[View Product on Wellcome]({TARGET_URL})"
    )
    send_telegram_alert(msg)


if __name__ == "__main__":
    main()
