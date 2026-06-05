import requests
import re
import os

URL = "https://www.goodreturns.in/gold-rates/coimbatore.html"
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def get_price():
    r = requests.get(URL, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    match = re.search(r"currentMetalPrices\s*=\s*\{[^}]+'22'\s*:\s*([\d]+)", r.text)
    if not match:
        raise Exception("22K price not found in page source")
    return match.group(1)

def parse_price(price_str):
    return round(float(str(price_str).replace("₹", "").replace(",", "").strip()), 2)

price_str = get_price()
current_price = parse_price(price_str)

try:
    with open("GoldPrice/last_price.txt") as f:
        content = f.read().strip()
        print(f"Read from file: '{content}'")
        last_price = parse_price(content)
except Exception as e:
    print(f"File read error: {e}")
    last_price = None

if last_price is None or current_price != last_price:
    if last_price is not None and current_price != last_price:
        diff = current_price - last_price
        if diff > 0:
            change_line = f"▲ Increased by ₹{diff:.0f}"
        else:
            change_line = f"▼ Decreased by ₹{abs(diff):.0f}"
        send_telegram(
            f"🔔 Gold Price Update – Coimbatore\n"
            f"22K: ₹{current_price:,.0f}\n"
            f"{change_line}"
        )
    elif last_price is None:
        send_telegram(
            f"🔔 Gold Price Update – Coimbatore\n"
            f"22K: ₹{current_price:,.0f}\n"
            f"ℹ️ First reading recorded"
        )
    with open("GoldPrice/last_price.txt", "w") as f:
        f.write(f"{current_price:.2f}")
