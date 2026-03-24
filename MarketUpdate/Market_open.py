"""
Market Open Snapshot — 9:20 AM IST
Fetches live Nifty 50, Sensex, Top 5 Gainers & Losers from Nifty 100.
Sends as image to Telegram.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils import *
from PIL import Image, ImageDraw
from datetime import datetime
import pytz
import requests

IST   = pytz.timezone("Asia/Kolkata")
TODAY = datetime.now(IST).strftime("%d %b %Y")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

NSE_BASE = "https://www.nseindia.com"

def get_nse_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get(NSE_BASE, timeout=10)
    return s

def fetch_indices(session):
    url = f"{NSE_BASE}/api/allIndices"
    r   = session.get(url, timeout=10)
    data = r.json()["data"]
    result = {}
    for idx in data:
        if idx["index"] in ("NIFTY 50", "NIFTY BANK", "NIFTY IT",
                             "NIFTY AUTO", "NIFTY FMCG", "NIFTY METAL",
                             "NIFTY REALTY", "NIFTY PHARMA"):
            result[idx["index"]] = {
                "last":    idx["last"],
                "change":  idx["variation"],
                "pct":     idx["percentChange"],
            }
    return result

def fetch_sensex():
    """Fetch Sensex from BSE via Yahoo Finance."""
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/^BSESN",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        j = r.json()
        price = j["chart"]["result"][0]["meta"]["regularMarketPrice"]
        prev  = j["chart"]["result"][0]["meta"]["previousClose"]
        return {"last": round(price, 2),
                "change": round(price - prev, 2),
                "pct": round((price - prev) / prev * 100, 2)}
    except:
        return None

def fetch_gainers_losers(session):
    """Top gainers and losers from Nifty 100."""
    gainers, losers = [], []
    try:
        url = f"{NSE_BASE}/api/live-analysis-variations?index=gainers"
        r   = session.get(url, timeout=10)
        data = r.json()
        # Filter Nifty 100 stocks
        for item in data.get("NIFTY100", {}).get("data", [])[:5]:
            gainers.append({
                "symbol": item["symbol"],
                "ltp":    item["ltp"],
                "pct":    item["perChange"],
            })
    except Exception as e:
        print(f"Gainers error: {e}")

    try:
        url = f"{NSE_BASE}/api/live-analysis-variations?index=losers"
        r   = session.get(url, timeout=10)
        data = r.json()
        for item in data.get("NIFTY100", {}).get("data", [])[:5]:
            losers.append({
                "symbol": item["symbol"],
                "ltp":    item["ltp"],
                "pct":    item["perChange"],
            })
    except Exception as e:
        print(f"Losers error: {e}")

    return gainers, losers

def build_image(indices, sensex, gainers, losers):
    W, H = 900, 560
    img  = Image.new("RGB", (W, H), BG)
    d    = ImageDraw.Draw(img)

    f_tiny   = load_font(15)
    f_small  = load_font(17)
    f_med    = load_font(20)
    f_large  = load_font(26, bold=True)
    f_xlarge = load_font(38, bold=True)
    f_bold   = load_font(22, bold=True)
    f_num    = load_font(30, bold=True)

    # Top bar
    d.rectangle([0, 0, W, 5], fill=GREEN)

    # Header
    rounded_rect(d, [18, 14, 882, 78], 12,
                 fill=(4, 22, 4), outline=(20, 80, 20), width=1)
    text(d, (30, 22), "📈  Market Open Snapshot", f_large, WHITE)
    text(d, (30, 54), f"Live data as of 9:20 AM IST · {TODAY}", f_small, GRAY)
    text(d, (860, 22), "9:20 AM IST", f_small, GRAY, anchor="ra")

    nifty = indices.get("NIFTY 50", {})

    # ── Nifty + Sensex cards ───────────────────────────────
    # Nifty card
    nifty_bull = nifty.get("change", 0) >= 0
    nifty_col  = GREEN if nifty_bull else RED
    nifty_bg   = (10, 30, 10) if nifty_bull else DARK_RED_BG
    nifty_bdr  = (30, 100, 30) if nifty_bull else BORDER_RED

    rounded_rect(d, [18, 88, 440, 210], 12,
                 fill=nifty_bg, outline=nifty_bdr, width=1)
    text(d, (30, 96), "NIFTY 50", f_med, GRAY)
    text(d, (30, 122), f"₹{nifty.get('last', 'N/A'):,.2f}", f_xlarge, nifty_col)
    chg  = nifty.get('change', 0)
    pct  = nifty.get('pct', 0)
    sym  = "▲" if chg >= 0 else "▼"
    text(d, (30, 172), f"{sym} {abs(chg):,.2f} pts  ({sym} {abs(pct):.2f}%)",
         f_bold, nifty_col)
    tag = "🟢 BULLISH" if nifty_bull else "🔴 BEARISH"
    text(d, (430, 96), tag, f_small,
         GREEN if nifty_bull else RED, anchor="ra")

    # Sensex card
    if sensex:
        s_bull = sensex["change"] >= 0
        s_col  = GREEN if s_bull else RED
        s_bg   = (10, 30, 10) if s_bull else DARK_RED_BG
        s_bdr  = (30, 100, 30) if s_bull else BORDER_RED
        rounded_rect(d, [460, 88, 882, 210], 12,
                     fill=s_bg, outline=s_bdr, width=1)
        text(d, (472, 96), "SENSEX (BSE)", f_med, GRAY)
        text(d, (472, 122), f"₹{sensex['last']:,.2f}", f_xlarge, s_col)
        sym2 = "▲" if sensex["change"] >= 0 else "▼"
        text(d, (472, 172),
             f"{sym2} {abs(sensex['change']):,.2f} pts  ({sym2} {abs(sensex['pct']):.2f}%)",
             f_bold, s_col)

    # ── Sector mini cards ─────────────────────────────────
    sectors = ["NIFTY BANK", "NIFTY IT", "NIFTY AUTO",
               "NIFTY METAL", "NIFTY FMCG", "NIFTY PHARMA"]
    sec_w = (W - 36 - 5*10) // 6
    for i, sec in enumerate(sectors):
        data = indices.get(sec, {})
        if not data:
            continue
        sx1 = 18 + i * (sec_w + 10)
        sy1 = 220
        sx2 = sx1 + sec_w
        sy2 = sy1 + 62
        is_up = data.get("pct", 0) >= 0
        bg = (10, 26, 10) if is_up else (26, 6, 6)
        bdr = (30, 80, 30) if is_up else (80, 20, 20)
        rounded_rect(d, [sx1, sy1, sx2, sy2], 8, fill=bg, outline=bdr, width=1)
        label = sec.replace("NIFTY ", "")
        text(d, ((sx1+sx2)//2, sy1+10), label, f_tiny, GRAY, anchor="mt")
        col = GREEN if is_up else RED
        sym3 = "▲" if is_up else "▼"
        text(d, ((sx1+sx2)//2, sy1+30),
             f"{sym3}{abs(data['pct']):.1f}%", f_small, col, anchor="mt")

    # ── Gainers & Losers ──────────────────────────────────
    col_w = 426
    gl_y  = 295

    # Gainers header
    rounded_rect(d, [18, gl_y, 18+col_w, gl_y+28], 8,
                 fill=(10, 35, 10), outline=(30, 90, 30), width=1)
    text(d, (18 + col_w//2, gl_y+14),
         "🟢  Top 5 Gainers — Nifty 100", f_small, GREEN, anchor="mm")

    # Losers header
    rounded_rect(d, [460, gl_y, 882, gl_y+28], 8,
                 fill=DARK_RED_BG, outline=BORDER_RED, width=1)
    text(d, (671, gl_y+14),
         "🔴  Top 5 Losers — Nifty 100", f_small, RED, anchor="mm")

    row_h = 42
    for i in range(5):
        ry = gl_y + 32 + i * row_h
        bg = (18, 18, 18) if i % 2 == 0 else CARD_BG

        # Gainer row
        if i < len(gainers):
            g = gainers[i]
            rounded_rect(d, [18, ry, 18+col_w, ry+row_h-2], 6, fill=bg)
            text(d, (28, ry+8), g["symbol"], f_med, WHITE)
            text(d, (28, ry+26), f"₹{g['ltp']:,.2f}", f_tiny, GRAY)
            pct_t = f"▲ {abs(g['pct']):.2f}%"
            pw = d.textlength(pct_t, font=f_bold)
            rounded_rect(d, [440-pw-24, ry+8, 440, ry+32], 6,
                         fill=(10, 35, 10))
            text(d, (440-12, ry+20), pct_t, f_bold, GREEN, anchor="rm")

        # Loser row
        if i < len(losers):
            l = losers[i]
            rounded_rect(d, [460, ry, 882, ry+row_h-2], 6, fill=bg)
            text(d, (470, ry+8), l["symbol"], f_med, WHITE)
            text(d, (470, ry+26), f"₹{l['ltp']:,.2f}", f_tiny, GRAY)
            pct_t2 = f"▼ {abs(l['pct']):.2f}%"
            pw2 = d.textlength(pct_t2, font=f_bold)
            rounded_rect(d, [882-pw2-24, ry+8, 882, ry+32], 6,
                         fill=RED_BG)
            text(d, (870, ry+20), pct_t2, f_bold, RED, anchor="rm")

    # Footer
    text(d, (W//2, H-14),
         f"Source: NSE India · Nifty 100 · {TODAY} · 9:20 AM IST",
         f_tiny, DARK_GRAY, anchor="ms")

    return img


def main():
    print("Fetching NSE data...")
    session = get_nse_session()
    indices = fetch_indices(session)
    sensex  = fetch_sensex()
    gainers, losers = fetch_gainers_losers(session)
    print(f"Nifty: {indices.get('NIFTY 50')}")
    print(f"Gainers: {len(gainers)}, Losers: {len(losers)}")

    img = build_image(indices, sensex, gainers, losers)
    send_image(img, caption=f"📈 Market Open Snapshot — {TODAY}")
    print("Market open image sent!")


if __name__ == "__main__":
    main()