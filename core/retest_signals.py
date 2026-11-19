"""Completed-bar setups for the catalog's two structural retest models."""

import numpy as np


def resistance_retest(df, name, params):
    high, low, close, atr = (df[column].to_numpy() for column in
                             ("high", "low", "close", "wilder_atr"))
    stops = np.full(len(df), np.nan)
    levels = np.full(len(df), np.nan)
    pivot = active = None
    for i in range(4, len(df)):
        center = i - 2
        if high[center] > max(high[i - 4], high[i - 3], high[i - 1], high[i]):
            pivot = center

        if active is not None:
            breakout, level, buffer = active
            if i - breakout > 10 or close[i] < level - buffer:
                active = None
            elif abs(low[i] - level) <= buffer and close[i] > level:
                stops[i] = low[i] - buffer
                levels[i] = level
                active = None
            continue

        if (pivot is not None and i - pivot <= 50 and np.isfinite(atr[i])
                and close[i - 1] <= high[pivot] < close[i]):
            active = (i, high[pivot], 0.25 * atr[i])
            pivot = None

    df[name] = np.isfinite(stops).astype(int)
    df["structural_stop"] = stops
    df["setup_level"] = levels
    return df


def demand_zone_retest(df, name, params):
    high, low, close, atr = (df[column].to_numpy() for column in
                             ("high", "low", "close", "wilder_atr"))
    stops = np.full(len(df), np.nan)
    levels = np.full(len(df), np.nan)
    zone = None
    for i in range(3, len(df)):
        base_low = min(low[i - 3:i])
        base_high = max(high[i - 3:i])
        frozen_atr = atr[i - 1]
        if (frozen_atr > 0 and base_high - base_low <= frozen_atr
                and close[i] >= base_high + 1.5 * frozen_atr):
            zone = (i, base_low, base_high, frozen_atr)
            continue

        if zone is None:
            continue
        created, lower, upper, zone_atr = zone
        if i - created > 20 or close[i] < lower:
            zone = None
        elif low[i] <= upper and high[i] >= lower:
            if close[i] > upper:
                stops[i] = lower - 0.25 * zone_atr
                levels[i] = upper
            zone = None

    df[name] = np.isfinite(stops).astype(int)
    df["structural_stop"] = stops
    df["setup_level"] = levels
    return df
