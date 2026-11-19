"""On-demand market context and optional publisher feeds."""

from datetime import timedelta
from urllib.parse import urlsplit

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

from core.data_loader import _standardize_ohlcv, get_symbol
from core.indicators import channel_breakout, wilder_atr


WATCHLIST = {
    "NQ": ("NQ=F", "Nasdaq 100"),
    "MNQ": ("MNQ=F", "Nasdaq 100"),
    "NAS100": (get_symbol("NAS100"), "Nasdaq 100"),
    "SPX500": (get_symbol("SPX500"), "S&P 500"),
    "XAUUSD": (get_symbol("XAUUSD"), "gold futures"),
    "EURUSD": (get_symbol("EURUSD"), "EUR/USD"),
    "GBPUSD": (get_symbol("GBPUSD"), "GBP/USD"),
    "BTCUSD": (get_symbol("BTCUSD"), "Bitcoin"),
}


@st.cache_data(ttl=300, show_spinner=False)
def _completed_bars(symbol, timeframe):
    bars = _standardize_ohlcv(yf.download(
        symbol, period="1mo", interval=timeframe, auto_adjust=False,
        progress=False, threads=False, timeout=10,
    ))
    if bars.empty or bars.index.tz is None:
        raise ValueError("No timestamped price bars returned.")
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(timeframe)
    bars = bars.loc[bars.index <= cutoff].copy()
    if len(bars) < 60:
        raise ValueError("At least 60 completed bars are needed for this brief.")
    return bars


@st.cache_data(ttl=300, show_spinner=False)
def _headlines(query, token):
    response = requests.get("https://api.marketaux.com/v1/news/all",
                            params={"api_token": token, "search": query, "language": "en",
                                    "limit": 3}, timeout=8)
    response.raise_for_status()
    return response.json()["data"][:3]


@st.cache_data(ttl=900, show_spinner=False)
def _calendar(token, today):
    end = today + timedelta(days=7)
    response = requests.get(f"https://api.tradingeconomics.com/calendar/country/united%20states/{today}/{end}",
                            params={"c": token, "importance": 3}, timeout=8)
    response.raise_for_status()
    now = pd.Timestamp.now(tz="UTC")
    events = []
    for event in response.json():
        date = pd.to_datetime(event.get("Date"), utc=True, errors="coerce")
        if pd.notna(date) and date >= now:
            events.append((date, event.get("Event", "Economic release")))
    return sorted(events)[:5]


def render_market_brief(key):
    st.subheader("Market Brief")
    left, right = st.columns(2)
    instrument = left.selectbox("Instrument", list(WATCHLIST), key=f"{key}_instrument")
    timeframe = right.selectbox("Timeframe", ["1h", "15m"], key=f"{key}_timeframe")
    selection = (instrument, timeframe)
    if st.button("Analyze now", key=f"{key}_analyze", type="primary"):
        st.session_state[f"{key}_requested"] = selection
    if st.session_state.get(f"{key}_requested") != selection:
        return

    symbol, query = WATCHLIST[instrument]
    try:
        with st.spinner("Loading market prices…"):
            bars = _completed_bars(symbol, timeframe)
    except Exception:
        bars = None
        st.warning(f"Price data for {symbol} is unavailable. Try another instrument or refresh later.")

    if bars is not None:
        latest = bars.iloc[-1]
        close = bars["close"]
        fast = close.ewm(span=20, adjust=False).mean().iloc[-1]
        slow = close.ewm(span=50, adjust=False).mean().iloc[-1]
        atr = wilder_atr(bars.copy(), "atr", {"length": 14})["atr"]
        relative_atr = atr / close
        ratio = relative_atr.iloc[-1] / relative_atr.iloc[-51:-1].median()
        bias = "Bullish" if latest.close > fast > slow else "Bearish" if latest.close < fast < slow else "Mixed"
        volatility = (
            "Unavailable" if pd.isna(ratio) or not 0 < ratio < float("inf")
            else "Elevated" if ratio > 1.25
            else "Subdued" if ratio < 0.75
            else "Typical"
        )
        end = bars.index[-1] + pd.Timedelta(timeframe)
        st.caption(f"Yahoo Finance · {symbol} · delay may apply · latest completed bar ended {end.isoformat()}")
        if pd.Timestamp.now(tz="UTC") - end > pd.Timedelta("4h"):
            st.info("The latest bar is more than four hours old. Check whether the market is closed or the feed is delayed.")
        for column, label, value in zip(st.columns(3),
                                         ("Latest close", "Price trend", "Volatility"),
                                         (f"{latest.close:,.4f}", bias, volatility)):
            column.metric(label, value)
        recent = bars.iloc[-21:-1]
        st.caption(f"Prior 20-bar range · Low {recent['low'].min():,.4f} · High {recent['high'].max():,.4f}")
        st.line_chart(close.tail(48), y_label="Close", height=200)
        st.caption("Trend compares the close with its 20- and 50-bar averages. Volatility compares ATR as a share of price with its recent median.")
        if instrument == "NAS100" and timeframe == "1h":
            high = bars["high"].iloc[-21:-1].max()
            triggered = bool(channel_breakout(bars.copy(), "signal", {"length": 20})["signal"].iloc[-1])
            st.write(f"**VA-002 entry condition:** {'Triggered on the latest close' if triggered else 'Waiting'} · prior 20-bar high {high:,.2f}.")
            st.caption("Checks the entry rule only. An existing position or execution constraints can block an entry.")

    try:
        config = st.secrets.get("market_brief", {})
    except FileNotFoundError:
        config = {}
    st.markdown("**Related headlines**")
    if news_key := config.get("marketaux_token"):
        try:
            news = _headlines(query, news_key)
            st.caption(f"Marketaux · matched to {query} · publisher timestamps shown")
            for item in news:
                st.text(f"{item['title']} · {item.get('source', 'Publisher')} · {item.get('published_at', '')}")
                url = item.get("url", "")
                if urlsplit(url).scheme in {"https", "http"}:
                    st.link_button("Read source", url)
            if not news:
                st.caption("No matching headlines returned.")
        except (requests.RequestException, ValueError, TypeError, KeyError):
            st.info("The headline feed is temporarily unavailable.")
    else:
        st.caption("News feed is not configured.")

    st.markdown("**Upcoming high-impact US releases**")
    if calendar_key := config.get("trading_economics_key"):
        try:
            events = _calendar(calendar_key, pd.Timestamp.now(tz="UTC").date())
            for date, name in events:
                st.text(f"{date:%d %b %H:%M} UTC · {name}")
            if not events:
                st.caption("No matching releases returned for the next week.")
            st.caption("Source: Trading Economics")
        except (requests.RequestException, ValueError, TypeError, KeyError):
            st.info("The economic calendar is temporarily unavailable.")
    else:
        st.caption("Economic calendar is not configured.")
