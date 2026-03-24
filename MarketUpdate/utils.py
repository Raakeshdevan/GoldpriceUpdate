import requests
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json

BOT_TOKEN = os.environ["BOT_TOKEN"]
MARKET_CHAT_ID = int(os.environ["MARKET_CHAT_ID"])

# ── Colors ──────────────────────────────────────────────
BG          = (15, 15, 15)
CARD_BG     = (22, 22, 22)
DARK_RED_BG = (30, 4, 4)
RED_BG      = (42, 8, 8)
RED         = (226, 75, 74)
RED_LIGHT   = (240, 149, 149)
RED_FAINT   = (252, 235, 235)
GREEN       = (99, 153, 34)
GREEN_LIGHT = (192, 221, 151)
WHITE       = (238, 238, 238)
GRAY        = (150, 150, 150)
DARK_GRAY   = (60, 60, 60)
BORDER      = (42, 42, 42)
BORDER_RED  = (90, 16, 16)
YELLOW      = (250, 199, 117)

def load_font(size, bold=False):
    paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans{'-Bold' if bold else '-Regular'}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill,
                           outline=outline, width=width)

def text(draw, pos, txt, font, color, anchor="la"):
    draw.text(pos, str(txt), font=font, fill=color, anchor=anchor)

def draw_tag(draw, x, y, label, bullish=True):
    color = GREEN if bullish else RED
    bg    = (10, 30, 10) if bullish else RED_BG
    f     = load_font(17, bold=True)
    w     = draw.textlength(label, font=f) + 20
    rounded_rect(draw, [x, y, x+w, y+22], 6, fill=bg)
    text(draw, (x + w//2, y + 11), label, f, color, anchor="mm")
    return w

def send_image(img: Image.Image, caption=""):
    buf = BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    requests.post(url, data={"chat_id": MARKET_CHAT_ID, "caption": caption},
                  files={"photo": ("market.png", buf, "image/png")})

def fetch_global_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {}
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/BZ=F",
                         headers=headers, timeout=10)
        j = r.json()
        price = j["chart"]["result"][0]["meta"]["regularMarketPrice"]
        prev  = j["chart"]["result"][0]["meta"]["previousClose"]
        data["crude"] = {"price": round(price, 2),
                         "change": round(price - prev, 2),
                         "pct": round((price - prev) / prev * 100, 2)}
    except:
        data["crude"] = None
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB",
                         headers=headers, timeout=10)
        j = r.json()
        price = j["chart"]["result"][0]["meta"]["regularMarketPrice"]
        prev  = j["chart"]["result"][0]["meta"]["previousClose"]
        data["dxy"] = {"price": round(price, 2),
                       "change": round(price - prev, 2),
                       "pct": round((price - prev) / prev * 100, 2)}
    except:
        data["dxy"] = None
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/^NSEI",
                         headers=headers, timeout=10)
        j = r.json()
        price = j["chart"]["result"][0]["meta"]["regularMarketPrice"]
        prev  = j["chart"]["result"][0]["meta"]["previousClose"]
        data["gift_nifty"] = {"price": round(price, 2),
                              "change": round(price - prev, 2),
                              "pct": round((price - prev) / prev * 100, 2)}
    except:
        data["gift_nifty"] = None
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F",
                         headers=headers, timeout=10)
        j = r.json()
        price = j["chart"]["result"][0]["meta"]["regularMarketPrice"]
        prev  = j["chart"]["result"][0]["meta"]["previousClose"]
        data["gold"] = {"price": round(price, 2),
                        "change": round(price - prev, 2),
                        "pct": round((price - prev) / prev * 100, 2)}
    except:
        data["gold"] = None
    return data