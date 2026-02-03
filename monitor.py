import requests
from bs4 import BeautifulSoup
import os

URL = "https://www.goodreturns.in/gold-rates/coimbatore.html"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
def get_price():
    r = requests.get(
        URL,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    soup = BeautifulSoup(r.text, "html.parser")

    # Find the correct section by heading text
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

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg
    })

price = get_price()

try:
    with open("last_price.txt") as f:
        last = f.read().strip()
except:
    last = ""

if price != last:
    send_telegram(f"🔔 Gold Price Update – Coimbatore\n22K: {price}")
    with open("last_price.txt", "w") as f:
        f.write(price)
