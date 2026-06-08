import pandas as pd


def detect_support(df, lookback=20):

    support = (
        df["low"]
        .rolling(lookback)
        .min()
    )

    return support


def detect_resistance(df, lookback=20):

    resistance = (
        df["high"]
        .rolling(lookback)
        .max()
    )

    return resistance


def add_support_resistance(df):

    df["support"] = detect_support(df)

    df["resistance"] = detect_resistance(df)

    return df
