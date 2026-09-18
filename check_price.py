import json
import os
import re
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Add any number of items to track in this list
ITEMS_TO_TRACK = [
    {
        "name": "原箱鈣思寶高鈣 植物固醇 24 X 250ML",
        "url": "https://www.wellcome.com.hk/zh-hant/p/%E5%8E%9F%E7%AE%B1%E9%88%A3%E6%80%9D%E5%AF%B6%E9%AB%98%E9%88%A3%20%E6%A4%8D%E7%89%A9%E5%9B%BA%E9%86%87%2024%20X%20250ML/i/113465289.html",
    },
        # {
    #     "name": "原箱鈣思寶 高蛋白質豆奶 24 X 250 ML",
    #     "url": "https://www.wellcome.com.hk/zh-hant/p/%E5%8E%9F%E7%AE%B1%E9%88%A3%E6%80%9D%E5%AF%B6%20%E9%AB%98%E8%9B%8B%E7%99%BD%E8%B3%AA%E8%B1%86%E5%A5%B6%2024%20X%20250%20ML/i/113719816.htmll"
    # },
      # {
    #     "name": "越南 業務用 原隻熟白蝦 1KG ",
    #     "url": "https://www.wellcome.com.hk/zh-hant/p/%E8%B6%8A%E5%8D%97%20%E6%A5%AD%E5%8B%99%E7%94%A8%20%E5%8E%9F%E9%9A%BB%E7%86%9F%E7%99%BD%E8%9D%A6%201KG%20(%E5%8C%85%E8%A3%9D%E5%8F%8A%E5%93%81%E7%89%8C%E9%9A%A8%E6%A9%9F%E7%99%BC%E6%94%BE)/i/113488734.html"
    # },
]


def fetch_price(url, fallback_name):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/124.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
  }
  res = requests.get(url, headers=headers, timeout=15)
  res.raise_for_status()
  soup = BeautifulSoup(res.text, "html.parser")

  for script in soup.find_all("script", type="application/ld+json"):
    try:
      data = json.loads(script.string)
      if data.get("@type") == "Product" or "offers" in data:
        raw_price = data.get("offers", {}).get("price")
        if raw_price:
          return {
              "name": data.get("name", fallback_name),
              "price": float(raw_price),
          }
    except Exception:
      continue

  prices = re.findall(r"\$\s*(\d+(?:\.\d{1,2})?)", soup.get_text())
  valid_prices = [float(p) for p in prices if float(p) > 5]
  if valid_prices:
    return {"name": fallback_name, "price": valid_prices[0]}

  raise ValueError(f"Could not extract price for {fallback_name}")


def send_telegram_alert(message):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
  }
  res = requests.post(url, json=payload, timeout=10)
  print(f"Telegram status: {res.status_code}")
  res.raise_for_status()


def main():
  report_lines = ["🛒 *Wellcome Price Update*\n"]

  for item in ITEMS_TO_TRACK:
    try:
      data = fetch_price(item["url"], item["name"])
      report_lines.append(
          f"📦 *{data['name']}*\n💰 Price: *${data['price']:.2f}*\n🔗 [Product"
          f" Link]({item['url']})\n"
      )
    except Exception as e:
      report_lines.append(f"⚠️ *{item['name']}*: Failed to fetch ({e})\n")

  full_message = "\n".join(report_lines)
  send_telegram_alert(full_message)


if __name__ == "__main__":
  main()
