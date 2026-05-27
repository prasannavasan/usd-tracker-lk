# USD Rate Tracker · Sri Lanka

Interactive chart tracking USD buying and selling rates at commercial banks in Sri Lanka (LKR) over the last 13 months.

**Live site:** https://prasannavasan.github.io/usd-tracker-lk/

## Features

- Today's buying rate, selling rate, spread, and 12-month change
- 13-month dual-line chart (buy + sell simultaneously) with shaded spread band
- Hover tooltips showing both rates + spread for each month
- Monthly data table with LIVE badge on the current month
- Zero dependencies — pure HTML/CSS/JS, single file

## Auto-update

A GitHub Actions workflow runs every day at **10:00 AM Sri Lanka time (UTC+5:30)**. It:

1. Fetches the USD/LKR mid-rate from [open.er-api.com](https://open.er-api.com) (free, no API key)
2. Derives buying and selling rates using a calibrated ±3.8 LKR half-spread
3. Updates `index.html` in place and commits the change
4. GitHub Pages redeploys automatically — live within ~2 minutes

The 10:00 AM schedule is 30 minutes after the Central Bank of Sri Lanka (CBSL) publishes official TT rates at 9:30 AM, ensuring the latest data is captured.

To trigger a manual update: [Actions → Update USD Rate → Run workflow](https://github.com/prasannavasan/usd-tracker-lk/actions/workflows/update-rate.yml)

## Data sources

**Historical data (May 2025 – Apr 2026):** Average monthly TT (Telegraphic Transfer) buying and selling rates from the [Central Bank of Sri Lanka](https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates/daily-buy-and-sell-exchange-rates). These are averages of daily quotes provided at 9:30 AM by commercial banks in Colombo.

**Live daily rate:** Mid-rate from [open.er-api.com](https://open.er-api.com) with a ±3.8 LKR spread. The spread is calibrated from CBSL TT data (recent months show a consistent 7.6 LKR sell–buy spread).

> Rates are indicative. Actual rates at your bank may differ slightly. For official rates visit [cbsl.gov.lk](https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates).
