"""On-demand market context and optional publisher feeds."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
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


CATALYSTS = (
    ("Rates & inflation", r"\b(fed|fomc|rate decision|rate cut[s]?|cpi|ppi|inflation|treasury yields?)\b"),
    ("Jobs & growth", r"\b(payrolls|jobs report|unemployment|jolts|gdp|recession)\b"),
    ("Earnings", r"\b(earnings|profit warning|revenue guidance)\b"),
    ("Index changes", r"\b(rebalance|rebalancing|reconstitution|index inclusion|join the nasdaq|added to the index)\b"),
    ("Policy & risk", r"\b(tariff[s]?|sanction[s]?|ban[s]?|regulation|ceasefire|shutdown)\b"),
)
BACKGROUND_NEWS = re.compile(r"\b(buy[- ]write|covered call[s]?|fund flows?|etf holdings|dividend yield)\b", re.I)


def _catalyst_topic(title):
    if BACKGROUND_NEWS.search(title):
        return None
    return next((topic for topic, pattern in CATALYSTS if re.search(pattern, title, re.I)), None)


def _recent_headlines(items, now):
    cutoff = now - pd.Timedelta(days=7)
    recent = []
    for item in items:
        published = pd.to_datetime(item.get("published_at"), utc=True, errors="coerce")
        title = (item.get("title") or "").strip()
        if title and pd.notna(published) and cutoff <= published <= now:
            recent.append({
                "title": title,
                "publisher": item.get("source") or "Publisher unavailable",
                "published": published,
                "preview": (item.get("description") or "").strip(),
                "topic": _catalyst_topic(title),
            })
    recent.sort(key=lambda item: item["published"], reverse=True)
    by_title = {}
    for item in recent:
        by_title.setdefault(item["title"].casefold(), item)
    return list(by_title.values())


@st.cache_data(ttl=300, show_spinner=False)
def _headlines(query, token):
    now = pd.Timestamp.now(tz="UTC")
    cutoff = now - pd.Timedelta(days=7)
    response = requests.get(
        "https://api.marketaux.com/v1/news/all",
        params={"api_token": token, "search": query, "language": "en",
                "published_after": cutoff.strftime("%Y-%m-%dT%H:%M:%S"), "limit": 3},
        timeout=8,
    )
    response.raise_for_status()
    return _recent_headlines(response.json()["data"], now)


BLS_CALENDAR_URL = "https://www.bls.gov/schedule/news_release/bls.ics"
BLS_RELEASES = (
    "Consumer Price Index", "Producer Price Index", "Employment Situation",
    "Job Openings and Labor Turnover", "Employment Cost Index",
)


def _parse_bls_calendar(content, now):
    if "BEGIN:VCALENDAR" not in content:
        raise ValueError("Invalid BLS calendar response.")
    unfolded = re.sub(r"\r?\n[ \t]", "", content)
    events = set()
    for match in re.finditer(r"BEGIN:VEVENT\r?\n(.*?)END:VEVENT", unfolded, re.DOTALL):
        event = match.group(1)
        summary = re.search(r"^SUMMARY:([^\r\n]+)", event, re.MULTILINE)
        start = re.search(r"^DTSTART;TZID=US-Eastern:(\d{8}T\d{6})", event, re.MULTILINE)
        if not summary or not start or re.search(r"^STATUS:CANCELLED\s*$", event, re.MULTILINE):
            continue
        title = summary.group(1)
        if not title.startswith(BLS_RELEASES):
            continue
        date = pd.Timestamp(datetime.strptime(start.group(1), "%Y%m%dT%H%M%S"),
                            tz=ZoneInfo("America/New_York")).tz_convert("UTC")
        if now <= date < now + pd.Timedelta(days=14):
            events.add((date, title))
    return sorted(events)[:8]


@st.cache_data(ttl=900, show_spinner=False)
def _calendar():
    response = requests.get(BLS_CALENDAR_URL, timeout=8)
    response.raise_for_status()
    return _parse_bls_calendar(response.text, pd.Timestamp.now(tz="UTC"))


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
        prices = close.tail(48)
        chart = go.Figure(go.Scatter(x=prices.index, y=prices, name="Close",
                                     line={"color": "#2563eb", "width": 2}))
        chart.update_layout(height=210, margin={"l": 0, "r": 12, "t": 8, "b": 4},
                            yaxis={"side": "right", "rangemode": "normal"},
                            hovermode="closest")
        st.plotly_chart(chart, use_container_width=True, key=f"{key}_price_chart",
                        config={"displayModeBar": False})
        st.caption("Trend compares the close with its 20- and 50-bar averages. Volatility compares ATR as a share of price with its recent median.")
        if instrument == "NAS100" and timeframe == "1h":
            high = bars["high"].iloc[-21:-1].max()
            triggered = bool(channel_breakout(bars.copy(), "signal", {"length": 20})["signal"].iloc[-1])
            st.write(f"**VA-002 entry condition:** {'Triggered on the latest close' if triggered else 'Waiting'} · prior 20-bar high {high:,.2f}.")
            st.caption("Checks the entry rule only. An existing position or execution constraints can block an entry.")

    st.markdown("**Next scheduled US releases**")
    try:
        events = _calendar()
        for date, name in events:
            eastern = date.tz_convert("America/New_York")
            st.text(f"{eastern:%d %b %H:%M %Z} · {name}")
        if not events:
            st.caption("No selected BLS releases are scheduled in the next 14 days.")
    except (requests.RequestException, ValueError):
        st.info("The BLS release calendar is temporarily unavailable.")
    st.caption("Source: US Bureau of Labor Statistics. Covers selected BLS releases.")

    try:
        config = st.secrets.get("market_brief", {})
    except FileNotFoundError:
        config = {}
    st.markdown("**Catalyst watch**")
    if news_key := config.get("marketaux_token"):
        try:
            news = _headlines(query, news_key)
            catalysts = [item for item in news if item["topic"]]
            background = [item for item in news if not item["topic"]]
            if not catalysts:
                st.info(f"No catalyst-tagged headlines for {query} in the latest feed results.")
            for item in catalysts:
                with st.container(border=True):
                    st.caption(item["topic"])
                    st.text(item["title"])
                    if item["preview"]:
                        st.text(item["preview"])
                    published = item["published"].strftime("%d %b, %H:%M UTC")
                    st.caption(f"{item['publisher']} · {published}")
            if background:
                with st.expander(f"Other matched headlines ({len(background)})"):
                    for item in background:
                        st.text(item["title"])
                        st.caption(f"{item['publisher']} · {item['published']:%d %b, %H:%M UTC}")
        except (requests.RequestException, ValueError, TypeError, KeyError):
            st.info("The headline feed is temporarily unavailable.")
    else:
        st.caption("News feed is not configured.")
