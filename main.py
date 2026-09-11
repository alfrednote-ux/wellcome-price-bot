import asyncio
import json
import logging
import os
import re
from aiohttp import web
from bs4 import BeautifulSoup
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TARGET_URL = "https://www.wellcome.com.hk/zh-hant/p/%E5%8E%9F%E7%AE%B1%E9%88%A3%E6%80%9D%E5%AF%B6%E9%AB%98%E9%88%A3%20%E6%A4%8D%E7%89%A9%E5%9B%BA%E9%86%87%2024%20X%20250ML/i/113465289.html"
PRICE_STORAGE_FILE = "calci_price.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def fetch_current_price():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/124.0.0.0 Safari/537.36"
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("👋 Bot is active! Send `/check` to get price.")


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("🔎 Fetching latest price from Wellcome...")
  try:
    curr = fetch_current_price()
    await update.message.reply_text(
        f"🛒 *{curr['name']}*\n💰 Price: *${curr['price']:.2f}*\n\n[Wellcome"
        f" Link]({TARGET_URL})",
        parse_mode="Markdown",
    )
  except Exception as e:
    await update.message.reply_text(f"❌ Failed: {e}")


# Dummy HTTP handler so Render Free Tier stays happy
async def handle_ping(request):
  return web.Response(text="Bot is running!")


async def main():
  # Start Telegram bot
  tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
  tg_app.add_handler(CommandHandler("start", start))
  tg_app.add_handler(CommandHandler("check", check))

  await tg_app.initialize()
  await tg_app.start()
  await tg_app.updater.start_polling()

  # Start dummy web server for Render
  port = int(os.environ.get("PORT", 8080))
  server = web.Application()
  server.router.add_get("/", handle_ping)
  runner = web.AppRunner(server)
  await runner.setup()
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()

  # Keep running
  while True:
    await asyncio.sleep(3600)


if __name__ == "__main__":
  asyncio.run(main())
