# core/data_loader.py
# VectorAlgoAI Market Data Loader
# MVP version: Yahoo Finance primary data source
#
# Supported markets:
#   Indices: NAS100, US30, SPX500
#   Gold:    XAUUSD
#   Forex:   EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD
#   Crypto:  BTCUSD, ETHUSD, SOLUSD, BNBUSD, XRPUSD
#
# Supported timeframes:
#   15m, 1h, 4h, 1d
#
# Notes:
#   - 4h candles are built by resampling 1h candles.
#   - Yahoo Finance has lookback limits for intraday data.
#   - This file removes Polygon/Massive dependency to avoid 429 rate-limit failures.

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, Tuple

import pandas as pd
import yfinance as yf


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


# -----------------------------------------------------------
# Yahoo Finance symbol mapper
# -----------------------------------------------------------
YF_SYMBOL_MAP: Dict[str, str] = {
    # Indices
    "NAS100": "^NDX",
    "US30": "^DJI",
    "SPX500": "^GSPC",

    # Gold proxy/futures
    "XAUUSD": "GC=F",
    "GOLD": "GC=F",

    # Forex
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "USDCHF": "CHF=X",
    "AUDUSD": "AUDUSD=X",

    # Crypto
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "SOLUSD": "SOL-USD",
    "BNBUSD": "BNB-USD",
    "XRPUSD": "XRP-USD",
}


# -----------------------------------------------------------
# Timeframe helpers
# -----------------------------------------------------------
def _normalize_timeframe(timeframe: str) -> str:
    tf = (timeframe or "1h").strip().lower()

    aliases = {
        "15min": "15m",
        "15": "15m",
        "1hr": "1h",
        "60m": "1h",
        "60min": "1h",
        "4hr": "4h",
        "240m": "4h",
        "1day": "1d",
        "d": "1d",
        "day": "1d",
    }

    return aliases.get(tf, tf)


def _yf_interval_for_timeframe(timeframe: str) -> str:
    """
    Yahoo does not provide native 4h candles.
    We download 1h and resample to 4h.
    """
    timeframe = _normalize_timeframe(timeframe)

    if timeframe == "15m":
        return "15m"
    if timeframe == "1h":
        return "1h"
    if timeframe == "4h":
        return "1h"
    if timeframe == "1d":
        return "1d"

    return "1h"


def _safe_period(timeframe: str, years: int) -> str:
    """
    Yahoo Finance has stricter limits for intraday data.
    We keep periods conservative so the MVP remains reliable.
    """
    timeframe = _normalize_timeframe(timeframe)
    years = max(1, int(years or 1))

    if timeframe == "15m":
        # Yahoo generally limits 15m intraday history.
        return "60d"

    if timeframe in ("1h", "4h"):
        # Usually supports up to about 730 days for hourly.
        if years <= 1:
            return "1y"
        return "2y"

    if timeframe == "1d":
        return f"{years}y"

    return "1y"


def get_symbol(symbol: str) -> str:
    """
    Convert user-facing symbols to Yahoo Finance symbols.
    Unknown symbols pass through directly, so stocks like AAPL/NVDA/TSLA still work.
    """
    raw = (symbol or "").strip().upper()
    return YF_SYMBOL_MAP.get(raw, raw)


# -----------------------------------------------------------
# Data cleanup
# -----------------------------------------------------------
def _flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinance sometimes returns MultiIndex columns.
    Flatten them safely.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[0]).lower().replace(" ", "_") for c in df.columns]
    else:
        df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    return df


def _standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure output columns:
    open, high, low, close, volume
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    df = df.copy()
    df = _flatten_yfinance_columns(df)

    # Some downloads may include adj_close but not adjusted close. We use close.
    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Downloaded data missing OHLC columns: {missing}")

    if "volume" not in df.columns:
        df["volume"] = 0

    df = df[["open", "high", "low", "close", "volume"]].copy()

    # Ensure datetime index, sorted and clean
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[~df.index.duplicated(keep="last")]
    df.index.name = "timestamp"

    return df


def _resample_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
    if df_1h is None or df_1h.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    df_4h = df_1h.resample("4h").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )

    df_4h = df_4h.dropna(subset=["open", "high", "low", "close"])
    df_4h.index.name = "timestamp"
    return df_4h


# -----------------------------------------------------------
# Cache helpers
# -----------------------------------------------------------
def _cache_path(symbol: str, timeframe: str) -> str:
    safe_symbol = (symbol or "UNKNOWN").upper().replace("/", "_").replace("=", "")
    safe_tf = _normalize_timeframe(timeframe)
    return os.path.join(DATA_DIR, f"{safe_symbol}_{safe_tf}_yf.csv")


def _read_cache(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        df = pd.read_csv(path, parse_dates=["timestamp"], index_col="timestamp")
        df = _standardize_ohlcv(df)
        return df
    except Exception:
        return pd.DataFrame()


def _write_cache(path: str, df: pd.DataFrame) -> None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        out = df.copy()
        out.index.name = "timestamp"
        out.to_csv(path)
    except Exception:
        pass


# -----------------------------------------------------------
# Main Yahoo fetcher
# -----------------------------------------------------------
def _fetch_yfinance(symbol: str, timeframe: str, years: int = 2) -> pd.DataFrame:
    yf_symbol = get_symbol(symbol)
    timeframe = _normalize_timeframe(timeframe)
    interval = _yf_interval_for_timeframe(timeframe)
    period = _safe_period(timeframe, years)

    raw = yf.download(
        yf_symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    df = _standardize_ohlcv(raw)

    if timeframe == "4h":
        df = _resample_4h(df)

    return df


# -----------------------------------------------------------
# Public API used by MVP dashboard
# -----------------------------------------------------------
def load_ohlcv(symbol: str, timeframe: str, years: int = 2) -> pd.DataFrame:
    """
    Load OHLCV candles for the selected market and timeframe.

    This function is intentionally simple for MVP:
    - Check local cache first
    - Fetch from Yahoo Finance if no cache
    - Return clean DataFrame with open/high/low/close/volume
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    timeframe = _normalize_timeframe(timeframe)
    path = _cache_path(symbol, timeframe)

    cached = _read_cache(path)
    if cached is not None and not cached.empty:
        return cached

    try:
        df = _fetch_yfinance(symbol, timeframe, years)
    except Exception as e:
        raise RuntimeError(
            f"Yahoo Finance data fetch failed for symbol={symbol}, timeframe={timeframe}. "
            f"Original error: {e}"
        )

    if df is None or df.empty:
        yf_symbol = get_symbol(symbol)
        raise RuntimeError(
            f"No Yahoo Finance data returned for symbol={symbol} mapped_to={yf_symbol}, timeframe={timeframe}. "
            "Try another market or timeframe."
        )

    _write_cache(path, df)
    return df


def supported_markets() -> Tuple[str, ...]:
    """
    Optional helper for future UI dropdowns.
    """
    return tuple(YF_SYMBOL_MAP.keys())
