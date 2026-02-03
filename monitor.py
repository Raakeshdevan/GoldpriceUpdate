import requests
from bs4 import BeautifulSoup
import os

URL = "https://www.goodreturns.in/gold-rates/coimbatore.html"

BOT_TOKEN = os.environ["7794314682:AAHmlLGeN-xmF4Pi5uJCPJszjBCxfEmGPZk"]
CHAT_ID = os.environ["820991371"]

def get_price():
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    row = soup.find("td", string="22 Carat")
    price = row.find_next("td").text.strip()
    return price

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
