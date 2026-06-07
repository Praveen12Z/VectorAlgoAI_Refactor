def execute_component(
    df,
    component
):

    name = component["component"]

    if name == "ema_trend":

        df["trend_long"] = (
            df["EMA50"] >
            df["EMA200"]
        )

    elif name == "rsi_filter":

        df["rsi_long"] = (
            df["RSI"] > 55
        )

    elif name == "pullback_entry":

        df["entry_pullback"] = (
            df["Close"] < df["EMA20"]
        )

    return df
