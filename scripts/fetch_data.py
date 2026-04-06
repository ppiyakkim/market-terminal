#!/usr/bin/env python3
"""
Market Terminal Data Fetcher
Pulls daily data from Yahoo Finance and writes JSON cache files.
Run via GitHub Actions daily after market close.
"""

import json
import time
import datetime
import yfinance as yf
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── UNIVERSE DEFINITIONS ─────────────────────────────────────────────────────

# Country → proxy ETF ticker (for index-level data)
COUNTRY_INDEX = {
    "US":     "^GSPC",
    "UK":     "^FTSE",
    "China":  "000001.SS",
    "Japan":  "^N225",
    "Europe": "^STOXX50E",
    "Korea":  "^KS11",
    "Brazil": "^BVSP",
    "Turkey": "XU100.IS",
    "Israel": "TA125.TA",
    "HongKong": "^HSI",
    "Taiwan": "^TWII",
    "Thailand": "^SET.BK",
}

# Country → representative large-cap holdings (MSCI-equivalent proxy)
# Sourced from iShares MSCI ETF holdings; update annually
COUNTRY_STOCKS = {
    "US": [
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","BRK-B","LLY","AVGO",
        "JPM","TSLA","UNH","V","XOM","MA","COST","JNJ","PG","HD",
        "NFLX","BAC","ABBV","KO","CRM","AMD","WMT","MRK","CVX","ORCL",
        "PEP","TMO","ACN","ADBE","MCD","QCOM","CSCO","IBM","TXN","NEE",
        "PM","GE","RTX","HON","INTC","AMGN","INTU","UNP","LOW","MDT",
    ],
    "UK": [
        "SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","RIO.L","GSK.L","DGE.L",
        "LSEG.L","NG.L","BARC.L","LLOY.L","CPG.L","REL.L","NWG.L","PRU.L",
        "VOD.L","AAL.L","ANTO.L","WPP.L","IMB.L","ABF.L","BATS.L","BT-A.L",
        "EXPN.L","LAND.L","SGE.L","SMT.L","SSE.L","SVT.L",
    ],
    "China": [
        "600519.SS","601398.SS","601288.SS","601939.SS","601628.SS",
        "600036.SS","601166.SS","600900.SS","601088.SS","601857.SS",
        "000858.SZ","000333.SZ","002594.SZ","300750.SZ","000725.SZ",
        "601318.SS","600276.SS","600887.SS","603288.SS","601012.SS",
    ],
    "Japan": [
        "7203.T","6758.T","8306.T","9432.T","6861.T","8035.T","9984.T",
        "6367.T","7974.T","8316.T","4519.T","6501.T","9433.T","8411.T",
        "7267.T","6954.T","4063.T","8766.T","6098.T","7741.T",
    ],
    "Korea": [
        "005930.KS","000660.KS","207940.KS","005380.KS","035420.KS",
        "051910.KS","006400.KS","035720.KS","028260.KS","012330.KS",
        "000270.KS","105560.KS","032830.KS","096770.KS","003550.KS",
        "011200.KS","017670.KS","030200.KS","009150.KS","086790.KS",
    ],
    "HongKong": [
        "0700.HK","0941.HK","1299.HK","0005.HK","0939.HK","2318.HK",
        "1398.HK","3690.HK","9988.HK","0883.HK","2020.HK","0388.HK",
        "1810.HK","0016.HK","1177.HK","2382.HK","0011.HK","2269.HK",
        "0960.HK","9618.HK",
    ],
    "Taiwan": [
        "2330.TW","2454.TW","2317.TW","2308.TW","2412.TW","2303.TW",
        "2882.TW","2881.TW","2891.TW","2886.TW","3711.TW","2002.TW",
        "1301.TW","1303.TW","2207.TW","2395.TW","3008.TW","2357.TW",
        "2408.TW","5880.TW",
    ],
    "Europe": [
        "ASML.AS","MC.PA","ROG.SW","NESN.SW","LVMH.PA","SIE.DE","SAP.DE",
        "SAN.MC","BNP.PA","AI.PA","TTE.PA","OR.PA","ABI.BR","BAYN.DE",
        "DTE.DE","IBE.MC","ALV.DE","ADS.DE","BBVA.MC","BMW.DE",
    ],
    "Brazil": [
        "VALE3.SA","PETR4.SA","ITUB4.SA","BBDC4.SA","ABEV3.SA","WEGE3.SA",
        "B3SA3.SA","RENT3.SA","SUZB3.SA","RDOR3.SA","GGBR4.SA","BRAP4.SA",
        "EQTL3.SA","CMIG4.SA","CPLE6.SA","CSAN3.SA","PRIO3.SA","ELET3.SA",
        "JBSS3.SA","MGLU3.SA",
    ],
    "Turkey": [
        "GARAN.IS","AKBNK.IS","THYAO.IS","EREGL.IS","BIMAS.IS","SAHOL.IS",
        "TUPRS.IS","KCHOL.IS","TOASO.IS","VESTL.IS","SISE.IS","HALKB.IS",
        "VAKBN.IS","YKBNK.IS","FROTO.IS","OTKAR.IS","PGSUS.IS","TCELL.IS",
        "ARCLK.IS","TTRAK.IS",
    ],
    "Israel": [
        "NICE","CHECK","CYBR","MNDY","GLBE","WIX","TEVA","ICL",
        "ESLT","CEVA","SPNS","KLAR","RADCOM","GILT","PERI",
    ],
    "Thailand": [
        "PTT.BK","ADVANC.BK","GULF.BK","CPALL.BK","AOT.BK","SCB.BK",
        "KBANK.BK","BBL.BK","INTUCH.BK","TRUE.BK","BDMS.BK","BH.BK",
        "CPN.BK","HMPRO.BK","IVL.BK","LH.BK","MINT.BK","PSH.BK","SCC.BK","TOP.BK",
    ],
}

# GICS sector codes mapped to display names
SECTOR_MAP = {
    "Technology": "Technology",
    "Financial Services": "Financials",
    "Healthcare": "Healthcare",
    "Consumer Cyclical": "Cons. Cyclical",
    "Industrials": "Industrials",
    "Communication Services": "Comm. Services",
    "Consumer Defensive": "Cons. Defensive",
    "Energy": "Energy",
    "Basic Materials": "Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
}

# Thematic ETFs (US-listed)
THEMATIC_ETFS = {
    "Sector": {
        "정보기술": "XLK",
        "헬스케어": "XLV",
        "금융": "XLF",
        "커뮤니케이션": "XLC",
        "소비순환재": "XLY",
        "경기방어주": "XLP",
        "산업재": "XLI",
        "유틸리티": "XLU",
        "에너지": "XLE",
        "리츠(섹터)": "XLRE",
        "소재": "XLB",
    },
    "Value/Growth": {
        "대형성장": "VUG",
        "중형성장": "IWP",
        "대형가치": "VTV",
        "중형가치": "VOE",
    },
    "Growth Themes": {
        "반도체": "SOXX",
        "클라우드": "SKYY",
        "인공지능": "AIQ",
        "사이버보안": "CIBR",
    },
    "Dividend": {
        "기술배당": "VIG",
        "배당성장": "SCHD",
        "리츠": "VNQ",
        "커버드콜": "JEPQ",
    },
    "Innovation": {
        "로봇": "BOTZ",
        "원전": "URA",
        "비트코인": "IBIT",
        "혁신": "ARKK",
    },
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def safe_pct(ticker_obj, period="1mo"):
    """Return period % change for a yf.Ticker. Returns None on failure."""
    try:
        hist = ticker_obj.history(period=period)
        if hist.empty or len(hist) < 2:
            return None
        start = hist["Close"].iloc[0]
        end = hist["Close"].iloc[-1]
        return round((end - start) / start * 100, 2)
    except Exception:
        return None


def get_pct_changes(ticker_obj):
    """Return dict of % changes across all periods."""
    result = {}
    # 1d needs intraday granularity
    try:
        hist_1d = ticker_obj.history(period="2d")
        if not hist_1d.empty and len(hist_1d) >= 2:
            prev = hist_1d["Close"].iloc[-2]
            last = hist_1d["Close"].iloc[-1]
            result["1d"] = round((last - prev) / prev * 100, 2)
        else:
            result["1d"] = None
    except Exception:
        result["1d"] = None

    for period, key in [("5d","1w"),("1mo","1mo"),("3mo","3mo"),("ytd","ytd"),("1y","1y")]:
        result[key] = safe_pct(ticker_obj, period)

    return result


def batch_fetch(tickers, delay=0.3):
    """Fetch ticker info + pct changes in bulk. Returns dict keyed by ticker."""
    out = {}
    for t in tickers:
        try:
            obj = yf.Ticker(t)
            info = obj.info
            changes = get_pct_changes(obj)
            out[t] = {
                "name": info.get("shortName") or info.get("longName") or t,
                "sector": SECTOR_MAP.get(info.get("sector",""), info.get("sector","")),
                "marketCap": info.get("marketCap"),
                "currency": info.get("currency","USD"),
                "changes": changes,
            }
        except Exception as e:
            out[t] = {"name": t, "sector": "", "marketCap": None, "currency": "", "changes": {}, "error": str(e)}
        time.sleep(delay)
    return out


# ── MAIN FETCH ROUTINES ───────────────────────────────────────────────────────

def fetch_country_indices():
    print("Fetching country indices...")
    result = {}
    for country, ticker in COUNTRY_INDEX.items():
        try:
            obj = yf.Ticker(ticker)
            changes = get_pct_changes(obj)
            result[country] = {"ticker": ticker, "changes": changes}
        except Exception as e:
            result[country] = {"ticker": ticker, "changes": {}, "error": str(e)}
        time.sleep(0.3)
    return result


def fetch_stock_universe():
    print("Fetching stock universe (this takes a while)...")
    result = {}
    for country, tickers in COUNTRY_STOCKS.items():
        print(f"  → {country} ({len(tickers)} stocks)")
        result[country] = batch_fetch(tickers, delay=0.25)
    return result


def fetch_etf_barometer():
    print("Fetching thematic ETFs...")
    all_tickers = []
    for group in THEMATIC_ETFS.values():
        all_tickers.extend(group.values())

    raw = batch_fetch(list(set(all_tickers)), delay=0.2)

    # Restructure with group labels
    result = {}
    for group_name, members in THEMATIC_ETFS.items():
        result[group_name] = {}
        for label, ticker in members.items():
            result[group_name][label] = {
                "ticker": ticker,
                **raw.get(ticker, {"changes": {}})
            }
    return result


def main():
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    indices = fetch_country_indices()
    stocks = fetch_stock_universe()
    etfs = fetch_etf_barometer()

    # Write individual cache files
    (DATA_DIR / "indices.json").write_text(
        json.dumps({"updated": timestamp, "data": indices}, ensure_ascii=False, indent=2)
    )
    (DATA_DIR / "stocks.json").write_text(
        json.dumps({"updated": timestamp, "data": stocks}, ensure_ascii=False, indent=2)
    )
    (DATA_DIR / "etfs.json").write_text(
        json.dumps({"updated": timestamp, "data": etfs}, ensure_ascii=False, indent=2)
    )

    # Combined manifest for the frontend
    manifest = {
        "updated": timestamp,
        "countries": list(COUNTRY_INDEX.keys()),
        "etfGroups": list(THEMATIC_ETFS.keys()),
    }
    (DATA_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )

    print(f"\nDone. Data written to {DATA_DIR}/ at {timestamp}")


if __name__ == "__main__":
    main()
