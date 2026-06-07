def parse_to_schema(text):

    schema = UniversalStrategy()

    txt = text.lower()

    if "ema" in txt:
        schema.add_component(
            "trend",
            "ema_trend"
        )

    if "rsi" in txt:
        schema.add_component(
            "confirmation",
            "rsi_filter"
        )

    if "pullback" in txt:
        schema.add_component(
            "entry",
            "pullback_entry"
        )

    return schema.to_dict()
