#!/usr/bin/env python3
"""
Fetches today's USD/LKR mid-rate and appends a new daily entry to index.html.
Entries older than 90 days are dropped automatically (rolling 3-month window).

Data between DATA_START and DATA_END markers is fully replaced each run.
"""

import re
import sys
import json
import urllib.request
from datetime import datetime, timezone, timedelta, date

# ── Time ──────────────────────────────────────────────────────────────────────

SL_TZ   = timezone(timedelta(hours=5, minutes=30))
now     = datetime.now(SL_TZ)
today   = now.date()
date_str = now.strftime(f"%b {now.day}, %Y")   # "May 27, 2026"

# ── Fetch mid-rate ────────────────────────────────────────────────────────────

HALF_SPREAD = 3.80   # calibrated from CBSL TT data (sell−buy ≈ 7.6 LKR)

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
    print(f"ERROR: rates out of sane range — aborting")
    sys.exit(1)

print(f"Mid {mid_lkr:.2f} | Buy {buy:.2f} | Sell {sell:.2f}")

# ── Parse current DATA from index.html ───────────────────────────────────────

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

block_match = re.search(
    r'(\[ // DATA_START\n)(.*?)(\n  \]; // DATA_END)',
    html, re.DOTALL
)
if not block_match:
    print("ERROR: DATA_START/DATA_END markers not found in index.html")
    sys.exit(1)

entries = []
for m in re.finditer(r'date: "(\d{4}-\d{2}-\d{2})", buy: ([\d.]+), sell: ([\d.]+)', block_match.group(2)):
    entries.append({
        "date": m.group(1),
        "buy":  float(m.group(2)),
        "sell": float(m.group(3)),
    })

# ── Add / update today's entry ────────────────────────────────────────────────

today_str = str(today)
existing  = next((e for e in entries if e["date"] == today_str), None)
if existing:
    existing["buy"]  = buy
    existing["sell"] = sell
    print(f"Updated existing entry for {today_str}")
else:
    entries.append({"date": today_str, "buy": buy, "sell": sell})
    print(f"Appended new entry for {today_str}")

# ── Drop entries older than 90 days ──────────────────────────────────────────

cutoff  = today - timedelta(days=90)
before  = len(entries)
entries = [e for e in entries if date.fromisoformat(e["date"]) >= cutoff]
entries.sort(key=lambda e: e["date"])
dropped = before - len(entries)
if dropped:
    print(f"Dropped {dropped} entries older than {cutoff}")

# ── Rebuild DATA block ────────────────────────────────────────────────────────

lines    = [f'    {{ date: "{e["date"]}", buy: {e["buy"]:.2f}, sell: {e["sell"]:.2f} }},' for e in entries]
new_block = "[ // DATA_START\n" + "\n".join(lines) + "\n  ]; // DATA_END"
html = html[:block_match.start()] + new_block + html[block_match.end():]

# ── Stat cards ────────────────────────────────────────────────────────────────

def patch(stat_id, value):
    global html
    html = re.sub(
        rf'(id="{stat_id}"[^>]*>)[^<]*(</div>)',
        rf'\g<1>{value}\g<2>',
        html,
    )

last  = entries[-1]
first = entries[0]
spread    = round(last["sell"] - last["buy"], 2)
change    = round(last["sell"] - first["sell"], 2)
sign      = "+" if change >= 0 else ""

patch("today-buy",      f'{last["buy"]:.2f}')
patch("today-sell",     f'{last["sell"]:.2f}')
patch("today-spread",   f'{spread:.2f}')
patch("period-change",  f'{sign}{change:.2f}')

# ── Date strings ──────────────────────────────────────────────────────────────

first_dt = datetime.strptime(entries[0]["date"],  "%Y-%m-%d")
last_dt  = datetime.strptime(entries[-1]["date"], "%Y-%m-%d")
start_mo = first_dt.strftime("%b %Y")
end_mo   = last_dt.strftime("%B %Y")

html = re.sub(
    r'(Last 3 months[^<]+)',
    f'Last 3 months — {start_mo} to {end_mo} &nbsp;·&nbsp; Updated {date_str}',
    html,
)
html = re.sub(
    r'(Last updated:\s*)[\w ,]+(\s*&nbsp;|<)',
    rf'\g<1>{date_str}\g<2>',
    html,
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Done — {len(entries)} entries | buy {buy:.2f} | sell {sell:.2f} | change {sign}{change:.2f}")
