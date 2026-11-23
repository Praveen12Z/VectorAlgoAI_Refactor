"""Load dated CME futures bars for the intraday backtester."""

import re

import pandas as pd


def fetch_futures_minutes(api_key, market, symbol, start_day, end_day):
    """Return a mapped one-minute CSV for inclusive New York session dates."""
    import databento as db

    if market not in ("MNQ", "MGC") or not re.fullmatch(market + r"[FGHJKMNQUVXZ]\d{1,4}", symbol):
        raise ValueError(f"Enter one dated {market} contract.")
    today = pd.Timestamp.now(tz="America/New_York").date()
    if not 0 <= (end_day - start_day).days < 31 or end_day >= today:
        raise ValueError("Choose up to 31 calendar days ending before today in New York.")
    start = pd.Timestamp(f"{start_day} 09:30", tz="America/New_York")
    end = pd.Timestamp(f"{end_day} 16:00", tz="America/New_York")
    try:
        data = db.Historical(api_key).timeseries.get_range(
            dataset="GLBX.MDP3", symbols=[symbol], stype_in="raw_symbol", schema="ohlcv-1m",
            start=start.tz_convert("UTC"), end=end.tz_convert("UTC"),
        ).to_df(price_type="float", pretty_ts=True, map_symbols=True)
    except (db.BentoError, OSError):
        raise ValueError("Databento could not load those bars. Check provider access, symbol, and dates.") from None
    if data.empty:
        raise ValueError("Databento returned no minute bars for that contract and date range.")
    return data.to_csv(index_label="ts_event").encode("utf-8")
