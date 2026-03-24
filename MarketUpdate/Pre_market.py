"""
Pre-Market Brief — 8:30 AM IST
Fetches global triggers, tags each bullish/bearish,
gives overall market prediction, sends as image to Telegram.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils import *
from PIL import Image, ImageDraw
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")
TODAY = datetime.now(IST).strftime("%d %b %Y")
WEEKDAY = datetime.now(IST).strftime("%A")

def arrow(val):
    return "▲" if val >= 0 else "▼"

def sign_color(val):
    return GREEN if val >= 0 else RED

def build_image(gdata):
    W, H = 900, 540
    img  = Image.new("RGB", (W, H), BG)
    d    = ImageDraw.Draw(img)

    # ── Fonts ──────────────────────────────────────────────
    f_tiny   = load_font(15)
    f_small  = load_font(17)
    f_med    = load_font(20)
    f_large  = load_font(26, bold=True)
    f_xlarge = load_font(34, bold=True)
    f_bold   = load_font(22, bold=True)

    # ── Top accent bar ─────────────────────────────────────
    d.rectangle([0, 0, W, 5], fill=RED)

    # ── Header ─────────────────────────────────────────────
    rounded_rect(d, [18, 14, 882, 80], 12,
                 fill=DARK_RED_BG, outline=BORDER_RED, width=1)
    text(d, (30, 22), f"🌅  Pre-Market Brief — {WEEKDAY}, {TODAY}",
         f_large, WHITE)
    text(d, (30, 54), "India Market Prediction · Before Market Opens",
         f_small, GRAY)
    text(d, (860, 22), "8:30 AM IST", f_small, GRAY, anchor="ra")

    # ── Global triggers grid ───────────────────────────────
    # Each trigger: title, value_str, change_str, bullish?
    triggers = []

    # Crude
    if gdata.get("crude"):
        c = gdata["crude"]
        bullish = c["change"] < 0          # lower crude = good for India
        triggers.append({
            "icon": "🛢",
            "title": "Brent Crude Oil",
            "value": f"${c['price']}",
            "change": f"{arrow(c['change'])} {abs(c['pct'])}%",
            "note": "High crude = inflation risk for India",
            "bullish": bullish
        })

    # Dollar Index
    if gdata.get("dxy"):
        c = gdata["dxy"]
        bullish = c["change"] < 0          # weaker dollar = FII inflows
        triggers.append({
            "icon": "💵",
            "title": "US Dollar Index (DXY)",
            "value": f"{c['price']}",
            "change": f"{arrow(c['change'])} {abs(c['pct'])}%",
            "note": "Strong dollar = FII outflows from India",
            "bullish": bullish
        })

    # GIFT Nifty
    if gdata.get("gift_nifty"):
        c = gdata["gift_nifty"]
        bullish = c["change"] >= 0
        triggers.append({
            "icon": "📊",
            "title": "Nifty 50 (Prev Close)",
            "value": f"₹{c['price']:,.0f}",
            "change": f"{arrow(c['change'])} {abs(c['pct'])}%",
            "note": "Early signal for today's opening",
            "bullish": bullish
        })

    # Gold
    if gdata.get("gold"):
        c = gdata["gold"]
        bullish = c["change"] < 0          # rising gold = fear = bad
        triggers.append({
            "icon": "🥇",
            "title": "Gold (Comex)",
            "value": f"${c['price']:,.0f}",
            "change": f"{arrow(c['change'])} {abs(c['pct'])}%",
            "note": "Rising gold = global fear = cautious market",
            "bullish": bullish
        })

    # ── Draw trigger cards (2 columns) ────────────────────
    card_w = 426
    card_h = 100
    gap    = 12
    start_y = 95

    for i, t in enumerate(triggers[:4]):
        col = i % 2
        row = i // 2
        x1  = 18 + col * (card_w + gap)
        y1  = start_y + row * (card_h + gap)
        x2  = x1 + card_w
        y2  = y1 + card_h

        rounded_rect(d, [x1, y1, x2, y2], 10, fill=CARD_BG,
                     outline=BORDER, width=1)

        # Left accent
        accent = GREEN if t["bullish"] else RED
        d.rounded_rectangle([x1, y1, x1+4, y2], radius=4, fill=accent)

        # Icon + title
        text(d, (x1+16, y1+12), t["icon"], f_med, WHITE)
        text(d, (x1+40, y1+12), t["title"], f_med, WHITE)

        # Value
        text(d, (x1+16, y1+42), t["value"], f_bold, WHITE)

        # Change
        chg_color = GREEN if t["bullish"] else RED
        text(d, (x1+16, y1+68), t["change"], f_small, chg_color)

        # Note
        text(d, (x1+card_w-10, y1+68), t["note"], f_tiny, GRAY, anchor="ra")

        # Tag
        tag_txt = "🟢 Bullish" if t["bullish"] else "🔴 Bearish"
        tag_col = GREEN if t["bullish"] else RED
        tag_bg  = (10, 30, 10) if t["bullish"] else RED_BG
        tw = d.textlength(tag_txt, font=f_tiny) + 16
        rounded_rect(d, [x2-tw-10, y1+10, x2-10, y1+30], 6, fill=tag_bg)
        text(d, (x2-tw//2-10, y1+20), tag_txt, f_tiny, tag_col, anchor="mm")

    # ── Overall Prediction bar ─────────────────────────────
    bullish_count  = sum(1 for t in triggers if t["bullish"])
    bearish_count  = len(triggers) - bullish_count
    overall_bull   = bullish_count > bearish_count
    pred_color     = GREEN if overall_bull else RED
    pred_bg        = (10, 40, 10) if overall_bull else (50, 8, 8)
    pred_border    = (30, 100, 30) if overall_bull else BORDER_RED
    pred_text      = "Market likely to open HIGHER today 🟢" if overall_bull \
                     else "Market likely to open LOWER today 🔴"
    score_txt      = f"{bullish_count} Bullish · {bearish_count} Bearish signals"

    pred_y = start_y + 2 * (card_h + gap) + 8
    rounded_rect(d, [18, pred_y, 882, pred_y+80], 12,
                 fill=pred_bg, outline=pred_border, width=1)
    text(d, (W//2, pred_y+20), "📈  Overall Prediction", f_med, GRAY, anchor="mt")
    text(d, (W//2, pred_y+44), pred_text, f_bold, pred_color, anchor="mt")
    text(d, (W//2, pred_y+66), score_txt, f_small, GRAY, anchor="mt")

    # ── Footer ─────────────────────────────────────────────
    text(d, (W//2, H-14), f"Sources: Yahoo Finance · NSE India · {TODAY} · 8:30 AM IST",
         f_tiny, DARK_GRAY, anchor="ms")

    return img


def main():
    print("Fetching global data...")
    gdata = fetch_global_data()
    print(f"Data: {gdata}")

    img = build_image(gdata)
    send_image(img, caption=f"🌅 Pre-Market Brief — {TODAY}")
    print("Pre-market image sent!")


if __name__ == "__main__":
    main()