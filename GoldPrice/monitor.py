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
    return float(price_str.replace("₹", "").replace(",", "").strip())

price_str = get_price()

try:
    with open("last_price.txt") as f:
        last_str = f.read().strip()
except:
    last_str = ""

if price_str != last_str:
    if last_str:
        diff = parse_price(price_str) - parse_price(last_str)
        if diff > 0:
            change_line = f"▲ Increased by ₹{diff:.0f}"
        else:
            change_line = f"▼ Decreased by ₹{abs(diff):.0f}"
    else:
        change_line = "ℹ️ First reading recorded"

    send_telegram(
        f"🔔 Gold Price Update – Coimbatore\n"
        f"22K: {price_str}\n"
        f"{change_line}"
    )
    with open("last_price.txt", "w") as f:
        f.write(price_str)
