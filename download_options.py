#!/usr/bin/env python3
"""Download Alphabet (GOOGL) options chain from Yahoo Finance and append to CSV."""

from datetime import datetime
from pathlib import Path
import sys
import pandas as pd
import yfinance as yf

TICKERS = ["GOOGL", "NFLX", "QQQ", "SPY"]
OUTPUT_CSV = Path(__file__).parent / "alphabet_options_chain.csv"


def fetch_options_chain(ticker_symbol: str = TICKER) -> pd.DataFrame:
    """Fetch all available call and put option chains for the given ticker."""
    ticker = yf.Ticker(ticker_symbol)
    expirations = ticker.options
    if not expirations:
        raise RuntimeError(f"No option expirations found for {ticker_symbol}")

    try:
        underlying_price = ticker.fast_info.get("lastPrice")
    except Exception:
        underlying_price = None

    now = datetime.now().astimezone()
    fetch_ts = now.isoformat(timespec="seconds")
    fetch_date = now.strftime("%Y-%m-%d")

    frames = []
    for exp in expirations:
        chain = ticker.option_chain(exp)
        for opt_type, df in (("call", chain.calls), ("put", chain.puts)):
            if df is None or df.empty:
                continue
            part = df.copy()
            part.insert(0, "option_type", opt_type)
            part.insert(0, "expiration", exp)
            part.insert(0, "underlying_price", underlying_price)
            part.insert(0, "ticker", ticker_symbol)
            part.insert(0, "fetch_date", fetch_date)
            part.insert(0, "fetch_timestamp", fetch_ts)
            frames.append(part)

    if not frames:
        raise RuntimeError(f"Empty options chain returned for {ticker_symbol}")

    return pd.concat(frames, ignore_index=True)


def main() -> int:
    frames = []
    for symbol in TICKERS:
        try:
            df = fetch_options_chain(symbol)
            print(f"Fetched {len(df)} option contracts for {symbol}")
            frames.append(df)
        except Exception as exc:
            print(f"Error fetching options chain for {symbol}: {exc}", file=sys.stderr)

    if not frames:
        return 1

    combined = pd.concat(frames, ignore_index=True)
    write_header = not OUTPUT_CSV.exists() or OUTPUT_CSV.stat().st_size == 0
    combined.to_csv(OUTPUT_CSV, mode="a", header=write_header, index=False)
    print(f"Saved {len(combined)} total option contracts to {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
