# Market Terminal

Personal Bloomberg-style market tracker. Static site hosted on GitHub Pages,
data refreshed daily via GitHub Actions.

## Stack

- **Frontend**: Vanilla HTML/JS + D3.js (no build step)
- **Data**: Yahoo Finance via `yfinance` Python library
- **Automation**: GitHub Actions (daily cron, weekdays)
- **Hosting**: GitHub Pages

## Features

- **Treemap**: Market-cap-weighted, drillable (Market → Sector → Stock)
  - Filter by country, period (1D / 1W / 1M / 3M / YTD / 1Y)
- **Sector Heatmap**: Country × Sector return matrix
- **ETF Barometer**: Thematic US-listed ETFs with inline bar charts
- **Global Indices**: 12 country indices, all periods

## Markets Covered

US · UK · China · Japan · Europe · Korea · Brazil · Turkey · Israel · Hong Kong · Taiwan · Thailand

## Setup

### 1. Clone & configure GitHub Pages

```bash
git clone https://github.com/YOUR_USERNAME/market-terminal
cd market-terminal
```

In repo Settings → Pages → Source: **Deploy from branch** → `main` → `/ (root)`.

### 2. Generate initial data (local)

```bash
pip install yfinance
python scripts/fetch_data.py
git add data/
git commit -m "chore: initial data"
git push
```

This takes ~5–10 minutes (Yahoo Finance rate limits).

### 3. GitHub Actions auto-updates

The workflow at `.github/workflows/daily_update.yml` runs at **23:00 UTC weekdays**
(30 min after NYSE close). No setup needed — it uses `GITHUB_TOKEN` automatically.

You can also trigger manually via Actions → "Daily Market Data Fetch" → "Run workflow".

### 4. Embed in Notion

In Notion, type `/embed`, paste your GitHub Pages URL:
```
https://YOUR_USERNAME.github.io/market-terminal/
```

Notion embeds work best at full-width. Set block width to max.

## Universe

Stock universe is based on iShares MSCI ETF holdings (top 20–50 per country).
Update `COUNTRY_STOCKS` in `scripts/fetch_data.py` annually or as needed.

## Data Caveats

- Yahoo Finance is an unofficial free API. Occasional failures are normal.
  The GitHub Action will silently skip failed tickers.
- Non-US market tickers use local exchange suffixes (.KS, .T, .HK, etc.).
- Israel stocks use US-listed ADRs for reliability.

## File Structure

```
market-terminal/
├── index.html                      ← Single-file frontend
├── data/
│   ├── manifest.json               ← Metadata
│   ├── indices.json                ← Country index returns
│   ├── stocks.json                 ← Per-stock data + returns
│   └── etfs.json                   ← Thematic ETF returns
├── scripts/
│   └── fetch_data.py               ← Data fetcher
└── .github/
    └── workflows/
        └── daily_update.yml        ← Automation
```
