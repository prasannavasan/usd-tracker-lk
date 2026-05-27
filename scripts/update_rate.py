#!/usr/bin/env python3
"""
Fetches the daily USD/LKR mid-rate from open.er-api.com and derives commercial
bank TT buying/selling rates using a calibrated spread from CBSL historical data.

Spread calibration (CBSL TT data, recent months):
  sell - buy ≈ 7.6 LKR consistently → half-spread = 3.8 LKR
  buy  = mid - 3.8
  sell = mid + 3.8

CBSL publishes TT rates at 9:30 AM Sri Lanka time. This script runs at 10:00 AM
SL time (4:30 AM UTC) so the latest rates are captured.
"""

import re
import sys
import json
import urllib.request
from datetime import datetime, timezone, timedelta

# ── Time ──────────────────────────────────────────────────────────────────────

SL_TZ = timezone(timedelta(hours=5, minutes=30))
now   = datetime.now(SL_TZ)

month_label  = now.strftime("%b '") + now.strftime("%y")   # "May '26"
date_str     = now.strftime(f"%b {now.day}, %Y")            # "May 27, 2026"
end_month    = now.strftime("%B %Y")
start_month  = (now - timedelta(days=365)).strftime("%B %Y")

# ── Fetch mid-rate ────────────────────────────────────────────────────────────

HALF_SPREAD = 3.80   # LKR — calibrated from CBSL TT data (recent spread ≈ 7.6)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "usd-tracker-bot/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

try:
    data    = fetch("https://open.er-api.com/v6/latest/USD")
    mid_lkr = float(data["rates"]["LKR"])
except Exception as e:
    print(f"ERROR fetching exchange rate: {e}")
    sys.exit(1)

buy  = round(mid_lkr - HALF_SPREAD, 2)
sell = round(mid_lkr + HALF_SPREAD, 2)

if not (100 < buy < 2000 and buy < sell):
    print(f"ERROR: rates out of sane range (buy={buy}, sell={sell}) — aborting")
    sys.exit(1)

print(f"Mid {mid_lkr:.2f} | Buy {buy:.2f} | Sell {sell:.2f} | Spread {sell-buy:.2f}")

# ── Update index.html ─────────────────────────────────────────────────────────

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Detect the current live entry's month
live_m     = re.search(r'month:\s*"([^"]+)"[^}]*live:\s*true', html)
live_month = live_m.group(1) if live_m else None

if live_month and live_month != month_label:
    # ── Month rollover ────────────────────────────────────────────────────────
    # 1. Strip ', live: true' from the old live entry
    html = re.sub(r',\s*live:\s*true', "", html, count=1)

    # 2. Drop the oldest DATA entry (first indented line)
    html = re.sub(
        r'    \{ month: "[^"]+",\s+buy:\s*[\d.]+,\s+sell:\s*[\d.]+,\s+note:\s*"[^"]*" \},\n',
        "",
        html,
        count=1,
    )

    # 3. Append new live entry before closing ];
    new_entry = (
        f'    {{ month: "{month_label}", buy: {buy}, sell: {sell}, '
        f'note: "Est. {date_str}", live: true }},\n'
    )
    html = html.replace("  ];\n", new_entry + "  ];\n", 1)
    print(f"Month rollover → added {month_label}")

else:
    # ── Daily update: patch the live entry ───────────────────────────────────
    def patch_live(m):
        s = re.sub(r'buy:\s*[\d.]+',   f'buy: {buy}',             m.group(0))
        s = re.sub(r'sell:\s*[\d.]+',  f'sell: {sell}',            s)
        s = re.sub(r'note:\s*"[^"]*"', f'note: "Est. {date_str}"', s)
        return s

    html = re.sub(r'\{[^}]*live:\s*true[^}]*\}', patch_live, html)

# ── Stat cards ────────────────────────────────────────────────────────────────

def patch_stat(stat_id, value):
    global html
    html = re.sub(
        rf'(id="{stat_id}"[^>]*>)[^<]*(</div>)',
        rf'\g<1>{value}\g<2>',
        html,
    )

spread_val  = round(sell - buy, 2)

# 12-month sell change: compare current sell to first sell in DATA
sell_vals  = [float(x) for x in re.findall(r'sell:\s*([\d.]+)', html)]
first_sell = sell_vals[0] if sell_vals else sell
yr_change  = round(sell - first_sell, 2)
yr_sign    = "+" if yr_change >= 0 else ""

patch_stat("today-buy",    f"{buy:.2f}")
patch_stat("today-sell",   f"{sell:.2f}")
patch_stat("today-spread", f"{spread_val:.2f}")
patch_stat("year-change",  f"{yr_sign}{yr_change:.2f}")

# ── Date strings ──────────────────────────────────────────────────────────────

html = re.sub(
    r"Last 13 months[^<]+",
    f"Last 13 months — {start_month} to {end_month} &nbsp;·&nbsp; Updated {date_str}",
    html,
)

html = re.sub(
    r"(Last updated:\s*)[\w ,]+(\s*&nbsp;|<)",
    rf"\g<1>{date_str}\g<2>",
    html,
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"index.html updated — buy {buy:.2f} | sell {sell:.2f} | yr-change {yr_sign}{yr_change:.2f}")
