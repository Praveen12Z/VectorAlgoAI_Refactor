# core/indicators.py

import pandas as pd

from core.retest_signals import demand_zone_retest, resistance_retest

from core.support_resistance import (
    add_support_resistance
)

# -------------------------------------------------------------
# Helper
# -------------------------------------------------------------
def _get_source(df: pd.DataFrame, source: str) -> pd.Series:

    if source not in df.columns:
        raise ValueError(
            f"Source column '{source}' not found in price data."
        )

    return df[source]


# -------------------------------------------------------------
# Indicator implementations
# -------------------------------------------------------------
def ema(
    df: pd.DataFrame,
    name: str,
    params: dict
) -> pd.DataFrame:

    src = _get_source(
        df,
        params.get("source", "close")
    )

    length = int(
        params.get("length", 20)
    )

    df[name] = src.ewm(
        span=length,
        adjust=False
    ).mean()

    return df


def sma(
    df: pd.DataFrame,
    name: str,
    params: dict
) -> pd.DataFrame:

    src = _get_source(
        df,
        params.get("source", "close")
    )

    length = int(
        params.get("length", 20)
    )

    df[name] = src.rolling(
        length
    ).mean()

    return df


def rsi(
    df: pd.DataFrame,
    name: str,
    params: dict
) -> pd.DataFrame:

    src = _get_source(
        df,
        params.get("source", "close")
    )

    length = int(
        params.get("length", 14)
    )

    delta = src.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.rolling(
        length
    ).mean()

    avg_loss = loss.rolling(
        length
    ).mean()

    rs = avg_gain / (
        avg_loss + 1e-10
    )

    df[name] = (
        100 - (
            100 / (1 + rs)
        )
    )

    return df


def atr(
    df: pd.DataFrame,
    name: str,
    params: dict
) -> pd.DataFrame:

    length = int(
        params.get("length", 14)
    )

    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)

    tr1 = (
        high - low
    ).abs()

    tr2 = (
        high - prev_close
    ).abs()

    tr3 = (
        low - prev_close
    ).abs()

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    df[name] = tr.rolling(
        length
    ).mean()

    return df


def bbands(
    df: pd.DataFrame,
    name: str,
    params: dict
) -> pd.DataFrame:

    src = _get_source(
        df,
        params.get("source", "close")
    )

    length = int(
        params.get("length", 20)
    )

    std_mult = float(
        params.get("std", 2.0)
    )

    band = params.get(
        "band",
        "middle"
    )

    ma = src.rolling(
        length
    ).mean()

    sd = src.rolling(
        length
    ).std()

    upper = ma + (
        sd * std_mult
    )

    lower = ma - (
        sd * std_mult
    )

    if band == "upper":
        df[name] = upper

    elif band == "lower":
        df[name] = lower

    else:
        df[name] = ma

    return df


# -------------------------------------------------------------
# Registry
# -------------------------------------------------------------
def channel_breakout(df, name, params):
    channel = df["high"].shift().rolling(params["length"]).max()
    df[name] = (df["close"].gt(channel) & df["close"].shift().le(channel)).astype(int)
    return df


def bollinger_squeeze(df, name, params):
    close = df["close"]
    window = close.rolling(params["length"])
    center = window.mean()
    deviation = 2 * window.std(ddof=0)
    upper = center + deviation
    width = (2 * deviation) / center
    threshold = width.rolling(120).quantile(0.20)
    df[name] = (width.shift().le(threshold.shift()) & close.gt(upper)
                & close.shift().le(upper.shift())).astype(int)
    return df


def wilder_atr(df, name, params):
    length = params["length"]
    previous = df["close"].shift()
    ranges = pd.concat([df["high"] - df["low"], (df["high"] - previous).abs(),
                       (df["low"] - previous).abs()], axis=1).max(axis=1)
    df[name] = _wilder_average(ranges, length)
    return df


def _wilder_average(values, length):
    seeded = values.copy()
    seeded.iloc[:length] = float("nan")
    if len(values) >= length:
        seeded.iloc[length - 1] = values.iloc[:length].mean()
    return seeded.ewm(alpha=1 / length, adjust=False).mean()


def wilder_rsi(df, name, params):
    length = params["length"]
    change = df["close"].diff().iloc[1:]
    gain = _wilder_average(change.clip(lower=0), length)
    loss = _wilder_average(-change.clip(upper=0), length)
    total = gain + loss
    df[name] = (100 * gain / total).mask(total.eq(0), 50)
    return df


INDICATOR_REGISTRY = {
    "resistance_retest": resistance_retest,
    "demand_zone_retest": demand_zone_retest,
    "channel_breakout": channel_breakout,
    "bollinger_squeeze": bollinger_squeeze,
    "wilder_atr": wilder_atr,
    "wilder_rsi": wilder_rsi,
    "ema": ema,
    "sma": sma,
    "rsi": rsi,
    "atr": atr,
    "bbands": bbands,
}


# -------------------------------------------------------------
# Generic indicator engine
# -------------------------------------------------------------
def apply_indicators(
    df: pd.DataFrame,
    indicator_dicts: list
) -> pd.DataFrame:

    df = df.copy()

    for icfg in indicator_dicts:

        name = icfg["name"]
        itype = icfg["type"]

        params = icfg.get(
            "params",
            {}
        )

        if itype not in INDICATOR_REGISTRY:

            raise ValueError(
                f"Unknown indicator type: {itype}"
            )

        func = INDICATOR_REGISTRY[
            itype
        ]

        df = func(
            df,
            name,
            params
        )

    return df


# -------------------------------------------------------------
# Compatibility bridge
# -------------------------------------------------------------
from core.strategy_config import (
    StrategyConfig
)


def apply_all_indicators(
    df: pd.DataFrame,
    cfg: StrategyConfig
) -> pd.DataFrame:

    indicator_dicts = []

    for ind in cfg.indicators:

        indicator_dicts.append(
            {
                "name": ind.name,
                "type": ind.type,
                "params": {
                    "length": ind.period,
                    "source": getattr(
                        ind,
                        "source",
                        "close"
                    ),
                },
            }
        )

    df = apply_indicators(
        df,
        indicator_dicts
    )

    # ---------------------------------
    # Universal Components
    # ---------------------------------

    df = add_support_resistance(
        df
    )

    return df
