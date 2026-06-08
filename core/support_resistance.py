import pandas as pd


def add_support_resistance(df, lookback=20, tolerance=0.002):
    df = df.copy()

    df["support"] = df["low"].rolling(lookback).min()
    df["resistance"] = df["high"].rolling(lookback).max()

    df["support_zone"] = df["support"] * (1 + tolerance)
    df["resistance_zone"] = df["resistance"] * (1 - tolerance)

    return df
