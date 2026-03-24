"""
End of Day Report — 8:30 PM IST
Scrapes top market news from Moneycontrol/ET Markets,
summarises what happened today, sends as image.
If no major news → sends a "quiet day" card.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils import *
from PIL import Image, ImageDraw
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import textwrap

IST   = pytz.timezone("Asia/Kolkata")
TODAY = datetime.now(IST).strftime("%d %b %Y")
WEEKDAY = datetime.now(IST).strftime("%A")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
NSE_BASE = "https://www.nseindia.com"

# ── Fetch closing data ─────────────────────────────────
def fetch_close_data():
    result = {}
    try:
        s = requests.Session()
        s.headers.update({**HEADERS, "Referer": NSE_BASE})
        s.get(NSE_BASE, timeout=10)
        r = s.get(f"{NSE_BASE}/api/allIndices", timeout=10)
        for idx in r.json()["data"]:
            if idx["index"] == "NIFTY 50":
                result["nifty"] = {
                    "last": idx["last"], "change": idx["variation"],
                    "pct": idx["percentChange"],
                    "high": idx.get("high", 0), "low": idx.get("low", 0),
                }
            if idx["index"] == "NIFTY BANK":
                result["banknifty"] = {"pct": idx["percentChange"]}
            if idx["index"] == "NIFTY IT":
                result["niftyit"] = {"pct": idx["percentChange"]}
    except Exception as e:
        print(f"Close data error: {e}")

    # Sensex
    try:
        r2 = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/^BSESN",
            headers=HEADERS, timeout=10)
        j  = r2.json()
        price = j["chart"]["result"][0]["meta"]["regularMarketPrice"]
        prev  = j["chart"]["result"][0]["meta"]["previousClose"]
        result["sensex"] = {
            "last": round(price, 2),
            "change": round(price - prev, 2),
            "pct": round((price - prev) / prev * 100, 2),
        }
    except:
        pass

    return result

# ── Scrape top headlines from ET Markets ──────────────
def fetch_news():
    headlines = []
    try:
        r = requests.get(
            "https://economictimes.indiatimes.com/markets/stocks/news",
            headers=HEADERS, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select("div.eachStory h3 a, article h3 a")[:8]:
            hl = item.get_text(strip=True)
            if hl and len(hl) > 20:
                headlines.append(hl)
    except Exception as e:
        print(f"ET news error: {e}")

    if not headlines:
        try:
            r = requests.get(
                "https://www.moneycontrol.com/news/business/markets/",
                headers=HEADERS, timeout=12)
            soup = BeautifulSoup(r.text, "html.parser")
            for item in soup.select("li.clearfix h2 a, .news_title a")[:8]:
                hl = item.get_text(strip=True)
                if hl and len(hl) > 20:
                    headlines.append(hl)
        except Exception as e:
            print(f"MC news error: {e}")

    # Deduplicate & trim
    seen = set()
    clean = []
    for h in headlines:
        h = h.strip()
        if h not in seen and len(h) > 15:
            seen.add(h)
            clean.append(h[:90] + ("…" if len(h) > 90 else ""))
    return clean[:5]

# ── Build image ────────────────────────────────────────
def build_image(close, headlines):
    W, H = 900, 580
    img  = Image.new("RGB", (W, H), BG)
    d    = ImageDraw.Draw(img)

    f_tiny   = load_font(15)
    f_small  = load_font(17)
    f_med    = load_font(20)
    f_large  = load_font(26, bold=True)
    f_xlarge = load_font(38, bold=True)
    f_bold   = load_font(22, bold=True)

    nifty = close.get("nifty", {})
    is_up = nifty.get("change", 0) >= 0

    # Top accent bar
    bar_color = GREEN if is_up else RED
    d.rectangle([0, 0, W, 5], fill=bar_color)

    # ── Header ─────────────────────────────────────────
    hdr_bg  = (4, 22, 4) if is_up else DARK_RED_BG
    hdr_bdr = (20, 80, 20) if is_up else BORDER_RED
    rounded_rect(d, [18, 14, 882, 80], 12,
                 fill=hdr_bg, outline=hdr_bdr, width=1)
    text(d, (30, 22), f"🌙  End of Day Report — {WEEKDAY}, {TODAY}",
         f_large, WHITE)
    text(d, (30, 54), "Indian Market Closing Summary", f_small, GRAY)
    text(d, (860, 22), "8:30 PM IST", f_small, GRAY, anchor="ra")

    # ── Nifty closing card ─────────────────────────────
    n_col = GREEN if is_up else RED
    n_bg  = (10, 30, 10) if is_up else DARK_RED_BG
    n_bdr = (30, 100, 30) if is_up else BORDER_RED
    rounded_rect(d, [18, 90, 440, 210], 12, fill=n_bg, outline=n_bdr, width=1)
    text(d, (30, 98), "NIFTY 50  CLOSE", f_med, GRAY)
    last = nifty.get("last", 0)
    text(d, (30, 124), f"₹{last:,.2f}", f_xlarge, n_col)
    chg = nifty.get("change", 0)
    pct = nifty.get("pct", 0)
    sym = "▲" if chg >= 0 else "▼"
    text(d, (30, 174), f"{sym} {abs(chg):,.2f} pts  ({sym} {abs(pct):.2f}%)",
         f_bold, n_col)
    tag = "🟢 CLOSED HIGHER" if is_up else "🔴 CLOSED LOWER"
    text(d, (430, 98), tag, f_small, n_col, anchor="ra")

    # ── Sensex closing card ────────────────────────────
    sensex = close.get("sensex", {})
    if sensex:
        s_up  = sensex.get("change", 0) >= 0
        s_col = GREEN if s_up else RED
        s_bg  = (10, 30, 10) if s_up else DARK_RED_BG
        s_bdr = (30, 100, 30) if s_up else BORDER_RED
        rounded_rect(d, [460, 90, 882, 210], 12,
                     fill=s_bg, outline=s_bdr, width=1)
        text(d, (472, 98), "SENSEX  CLOSE", f_med, GRAY)
        text(d, (472, 124), f"₹{sensex['last']:,.2f}", f_xlarge, s_col)
        sym2 = "▲" if sensex["change"] >= 0 else "▼"
        text(d, (472, 174),
             f"{sym2} {abs(sensex['change']):,.2f}  ({sym2} {abs(sensex['pct']):.2f}%)",
             f_bold, s_col)

    # ── Sector mini summary ────────────────────────────
    sectors = [
        ("Bank Nifty", close.get("banknifty", {}).get("pct", 0)),
        ("Nifty IT",   close.get("niftyit", {}).get("pct", 0)),
    ]
    sec_y = 220
    sec_w = 210
    for i, (name, pct_val) in enumerate(sectors):
        sx1 = 18 + i * (sec_w + 10)
        sx2 = sx1 + sec_w
        up  = pct_val >= 0
        rounded_rect(d, [sx1, sec_y, sx2, sec_y+50], 8,
                     fill=(10, 26, 10) if up else (26, 6, 6),
                     outline=(30, 80, 30) if up else (80, 20, 20), width=1)
        text(d, (sx1+10, sec_y+8), name, f_small, GRAY)
        col2 = GREEN if up else RED
        sym3 = "▲" if up else "▼"
        text(d, (sx1+10, sec_y+28), f"{sym3} {abs(pct_val):.2f}%",
             f_bold, col2)

    # ── News section ───────────────────────────────────
    news_y = 282
    rounded_rect(d, [18, news_y, 882, news_y+28], 8,
                 fill=CARD_BG, outline=BORDER, width=1)
    text(d, (W//2, news_y+14),
         "📰  Today's Major Market Headlines", f_small, GRAY, anchor="mm")

    if not headlines:
        # Quiet day card
        rounded_rect(d, [18, news_y+34, 882, news_y+130], 10,
                     fill=CARD_BG, outline=BORDER, width=1)
        text(d, (W//2, news_y+80),
             "No major updates today — quiet session 😴",
             f_bold, GRAY, anchor="mm")
    else:
        row_h = 50
        for i, hl in enumerate(headlines[:5]):
            ry  = news_y + 34 + i * row_h
            rbg = (18, 18, 18) if i % 2 == 0 else CARD_BG
            rounded_rect(d, [18, ry, 882, ry+row_h-2], 6, fill=rbg)

            # Bullet
            bullet_col = GREEN if is_up else RED
            d.ellipse([28, ry+18, 36, ry+26], fill=bullet_col)

            # Headline text (wrap if long)
            lines = textwrap.wrap(hl, width=90)
            for li, line in enumerate(lines[:2]):
                text(d, (44, ry + 8 + li*18), line,
                     f_small if li == 0 else f_tiny,
                     WHITE if li == 0 else GRAY)

    # ── Footer ─────────────────────────────────────────
    text(d, (W//2, H-14),
         f"Sources: ET Markets · Moneycontrol · NSE India · {TODAY} · EOD",
         f_tiny, DARK_GRAY, anchor="ms")

    return img


def main():
    print("Fetching EOD data...")
    close     = fetch_close_data()
    headlines = fetch_news()
    print(f"Nifty close: {close.get('nifty')}")
    print(f"Headlines: {len(headlines)}")

    img = build_image(close, headlines)
    send_image(img, caption=f"🌙 EOD Report — {TODAY}")
    print("EOD image sent!")


if __name__ == "__main__":
    main()  