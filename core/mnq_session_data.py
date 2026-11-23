"""Normalize MNQ exports and build complete New York session bars."""
from csv import reader
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO, StringIO

import numpy as np
import pandas as pd


_TIME_ZONE = "America/New_York"
_COLUMNS = ("stamp", "open", "high", "low", "close", "volume")
_ONE_MINUTE = pd.Timedelta(minutes=1)


def load_minutes(raw: bytes) -> pd.DataFrame:
    rows = []
    for line, row in enumerate(reader(StringIO(raw.decode("utf-8-sig")), delimiter=";"), 1):
        if not row:
            continue
        if len(row) != len(_COLUMNS):
            raise ValueError(f"Line {line} must contain a timestamp and five OHLCV fields.")
        rows.append(row)
    if not rows:
        raise ValueError("No minute candles found.")

    bars = pd.DataFrame(rows, columns=_COLUMNS)
    stamps = pd.to_datetime(bars.pop("stamp"), format="%Y%m%d %H%M%S", utc=True)
    return _minute_end_bars(bars, pd.DatetimeIndex(stamps))


def _minute_end_bars(bars: pd.DataFrame, stamps: pd.DatetimeIndex) -> pd.DataFrame:
    if bars.empty:
        raise ValueError("No minute candles found.")
    if stamps.hasnans or not (stamps == stamps.floor("min")).all():
        raise ValueError("Each timestamp must identify a whole UTC minute end.")
    duplicates = stamps[stamps.duplicated()]
    if not duplicates.empty:
        raise ValueError(f"Duplicate UTC minute-end timestamp: {duplicates[0].isoformat()}.")

    bars = bars.apply(pd.to_numeric, errors="raise")
    if (not np.isfinite(bars.to_numpy()).all()
            or (bars.high < bars[["open", "low", "close"]].max(axis=1)).any()
            or (bars.low > bars[["open", "close"]].min(axis=1)).any()
            or (bars.low <= 0).any() or (bars.volume < 0).any()):
        raise ValueError("Invalid OHLCV price range or volume.")
    bars.index = stamps.tz_convert(_TIME_ZONE).rename("stamp")
    return bars.sort_index()


@dataclass(frozen=True)
class MnqSession:
    """One observed weekday session, with its actual and missing minute ends."""

    date: pd.Timestamp
    minutes: pd.DataFrame
    missing_minutes: pd.DatetimeIndex

    @property
    def complete(self) -> bool:
        return self.missing_minutes.empty

    def candles(self, timeframe_minutes: int) -> pd.DataFrame:
        """Build close-stamped 5- or 15-minute candles for one complete session."""
        if timeframe_minutes not in (5, 15):
            raise ValueError("MNQ session candles support 5 or 15 minutes.")
        if not self.complete:
            raise ValueError(f"The {self.date.date()} session has missing minutes.")
        return self.minutes.resample(f"{timeframe_minutes}min", closed="right", label="right").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        )


@dataclass(frozen=True)
class MnqSessionData:
    minutes: pd.DataFrame
    sessions: tuple[MnqSession, ...]
    weekdays_without_session_rows: tuple[str, ...]
    dataset_sha256: str

    @property
    def complete_sessions(self) -> tuple[MnqSession, ...]:
        return tuple(session for session in self.sessions if session.complete)


def load_mnq_sessions(raw: bytes) -> MnqSessionData:
    """Check weekday 09:30–16:00 sessions against the full minute grid.

    Dates without rows are observations about export coverage. The import
    does not infer whether an exchange was scheduled to open on those dates.
    """
    return _build_sessions(load_minutes(raw), raw)


def load_broker_minute_sessions(raw: bytes) -> MnqSessionData:
    """Load broker candles with an explicit timezone and minute-start timestamps."""
    frame = pd.read_csv(BytesIO(raw))
    prices = list(_COLUMNS[1:-1])
    if not {"timestamp", *prices}.issubset(frame.columns):
        raise ValueError("Broker CSV must include timestamp, open, high, low and close.")
    timestamps = frame.timestamp.astype("string")
    if not timestamps.str.contains(r"(?:Z|[+-]\d{2}:\d{2})$", na=False).all():
        raise ValueError("Broker timestamps must have an explicit timezone offset or Z.")
    starts = pd.DatetimeIndex(pd.to_datetime(timestamps, format="ISO8601", utc=True))
    values = frame[prices].assign(volume=frame.get("volume", 0))
    return _build_sessions(_minute_end_bars(values, starts + _ONE_MINUTE), raw)


def load_databento_mnq_sessions(raw: bytes, *, raw_symbol: str) -> MnqSessionData:
    """Load an ohlcv-1m CSV exported from a Databento dataframe.

    Export with mapped symbols, decimal prices, and tz-aware ISO minute starts
    in the ts_event column. Request one dated raw symbol per export.
    """
    frame = pd.read_csv(BytesIO(raw))
    required = {"ts_event", "symbol", "instrument_id", *_COLUMNS[1:]}
    if not required.issubset(frame.columns):
        raise ValueError("Databento CSV must include ts_event, symbol, instrument_id and OHLCV.")
    if frame.empty:
        raise ValueError("No minute candles found.")
    if not frame.symbol.eq(raw_symbol).all() or frame.symbol.isna().any():
        raise ValueError(f"Databento CSV must contain only {raw_symbol}.")
    instrument_ids = pd.to_numeric(frame.instrument_id, errors="raise")
    if (instrument_ids.isna().any() or instrument_ids.nunique() != 1
            or not instrument_ids.gt(0).all() or not instrument_ids.mod(1).eq(0).all()):
        raise ValueError("Databento CSV must contain one valid instrument ID.")
    timestamp_text = frame.ts_event.astype("string")
    if not timestamp_text.str.contains(r"(?:Z|[+-]\d{2}:\d{2})$", na=False).all():
        raise ValueError("Databento ts_event must use ISO timestamps with explicit timezone offsets.")
    starts = pd.DatetimeIndex(pd.to_datetime(timestamp_text, format="ISO8601", utc=True))
    bars = _minute_end_bars(frame.loc[:, list(_COLUMNS[1:])], starts + _ONE_MINUTE)
    return _build_sessions(bars, raw)


def _build_sessions(bars: pd.DataFrame, raw: bytes) -> MnqSessionData:
    regular = bars.between_time("09:30", "16:00", inclusive="right")
    sessions = []
    for date, minutes in regular.groupby(regular.index.normalize()):
        if date.weekday() >= 5:
            continue
        expected = pd.date_range(
            date.replace(hour=9, minute=31), date.replace(hour=16), freq=_ONE_MINUTE
        )
        sessions.append(MnqSession(date, minutes, expected.difference(minutes.index)))

    observed = {session.date for session in sessions}
    weekdays = pd.bdate_range(bars.index[0].normalize(), bars.index[-1].normalize())
    absent = tuple(str(day.date()) for day in weekdays if day not in observed)
    return MnqSessionData(bars, tuple(sessions), absent, sha256(raw).hexdigest())
