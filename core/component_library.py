# core/component_library.py

COMPONENT_LIBRARY = {

    # --------------------------------
    # TREND
    # --------------------------------

    "ema_trend": {
        "category": "trend",
        "description": "EMA trend alignment"
    },

    "trendline": {
        "category": "trend",
        "description": "Trendline direction"
    },

    # --------------------------------
    # ENTRY
    # --------------------------------

    "pullback_entry": {
        "category": "entry",
        "description": "Pullback entry"
    },

    "breakout": {
        "category": "entry",
        "description": "Breakout entry"
    },

    "support_resistance": {
        "category": "entry",
        "description": "Support / Resistance"
    },

    # --------------------------------
    # CONFIRMATION
    # --------------------------------

    "rsi_filter": {
        "category": "confirmation",
        "description": "RSI filter"
    },

    "volume_filter": {
        "category": "confirmation",
        "description": "Volume confirmation"
    },

    "atr_filter": {
        "category": "confirmation",
        "description": "Volatility filter"
    },

    # --------------------------------
    # SESSION
    # --------------------------------

    "session_filter": {
        "category": "session",
        "description": "London / NY Session"
    },

    # --------------------------------
    # NEWS
    # --------------------------------

    "news_filter": {
        "category": "news",
        "description": "Avoid high-impact news"
    },

    # --------------------------------
    # PRICE ACTION
    # --------------------------------

    "bullish_engulfing": {
        "category": "price_action",
        "description": "Bullish engulfing candle"
    },

    "bearish_engulfing": {
        "category": "price_action",
        "description": "Bearish engulfing candle"
    },

    "pin_bar": {
        "category": "price_action",
        "description": "Pin bar rejection"
    },

    # --------------------------------
    # SMC / ICT
    # --------------------------------

    "liquidity_sweep": {
        "category": "smc",
        "description": "Liquidity sweep"
    },

    "order_block": {
        "category": "smc",
        "description": "Order block"
    },

    "fair_value_gap": {
        "category": "smc",
        "description": "Fair value gap"
    },

    "bos": {
        "category": "smc",
        "description": "Break of structure"
    },

    "choch": {
        "category": "smc",
        "description": "Change of character"
    },

    # --------------------------------
    # RISK
    # --------------------------------

    "atr_stop": {
        "category": "risk",
        "description": "ATR stop"
    },

    "rr_target": {
        "category": "risk",
        "description": "Reward/Risk target"
    }
}
