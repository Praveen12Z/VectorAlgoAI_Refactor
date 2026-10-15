"""Causal rolling support/resistance levels and closed-bar price-action signals.

All levels for bar t use bars strictly before t. Signals are evaluated at bar close.
"""
import pandas as pd


def add_support_resistance(df, lookback=20, tolerance=0.002):
    if lookback < 2 or not 0 <= tolerance < 1:
        raise ValueError("Invalid support/resistance lookback or tolerance")
    df = df.copy()
    prior_low = df["low"].shift(1)
    prior_high = df["high"].shift(1)
    df["support"] = prior_low.rolling(lookback, min_periods=lookback).min()
    df["resistance"] = prior_high.rolling(lookback, min_periods=lookback).max()
    df["support_zone"] = df["support"] * (1 + tolerance)
    df["resistance_zone"] = df["resistance"] * (1 - tolerance)

    # Breakout uses the last completed candle's established level.
    df["sr_breakout_long"] = (df["close"] > df["resistance"]) & (df["close"].shift(1) <= df["resistance"])
    df["sr_breakout_short"] = (df["close"] < df["support"]) & (df["close"].shift(1) >= df["support"])

    # Rejection: intrabar touch of a previously known zone, followed by a close away.
    df["sr_support_rejection"] = (df["low"] <= df["support_zone"]) & (df["close"] > df["support_zone"])
    df["sr_resistance_rejection"] = (df["high"] >= df["resistance_zone"]) & (df["close"] < df["resistance_zone"])
    return df
