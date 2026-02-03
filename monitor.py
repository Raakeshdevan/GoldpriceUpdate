import requests
from bs4 import BeautifulSoup
import os

URL = "https://www.goodreturns.in/gold-rates/coimbatore.html"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def get_price():
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    for td in soup.find_all("td"):
        text = td.get_text(strip=True)
        if "22" in text and "Carat" in text:
            price_td = td.find_next_sibling("td")
            if price_td:
                return price_td.get_text(strip=True)

    raise Exception("22K price not found")

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
