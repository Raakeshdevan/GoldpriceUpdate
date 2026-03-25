import requests
from bs4 import BeautifulSoup
import os

URL = "https://www.goodreturns.in/gold-rates/coimbatore.html"
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def get_price():
    r = requests.get(URL, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    section = soup.find(
        "section",
        attrs={"data-gr-title": lambda x: x and "22 Carat Gold Price" in x}
    )
    if not section:
        raise Exception("22K section not found")
    table = section.find("table")
    if not table:
        raise Exception("Price table not found")
    for row in table.tbody.find_all("tr"):
        cols = row.find_all("td")
        if cols[0].get_text(strip=True) == "1":
            return cols[1].get_text(strip=True)
    raise Exception("1 gram price not found")

def parse_price(price_str):
    return round(float(str(price_str).replace("₹", "").replace(",", "").strip()), 2)

price_str = get_price()
current_price = parse_price(price_str)

try:
    with open("GoldPrice/last_price.txt") as f:
        last_price = parse_price(f.read().strip())
except:
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