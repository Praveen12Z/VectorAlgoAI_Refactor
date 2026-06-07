# core/market_fit_analyzer.py

from core.data_loader import load_ohlcv
from core.indicators import apply_all_indicators
from core.backtester_adapter import run_backtest_v2


MARKETS = [
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "NAS100",
    "US30",
    "BTCUSD",
    "ETHUSD",
]


def analyze_market_fit(cfg, years=2):

    results = []

    for market in MARKETS:

        try:

            cfg.market = market

            df = load_ohlcv(
                market,
                cfg.timeframe,
                years
            )

            if df is None or df.empty:
                continue

            df = apply_all_indicators(
                df,
                cfg
            )

            metrics, _, _, _ = run_backtest_v2(
                df,
                cfg
            )

            results.append(
                {
                    "market": market,
                    "profit_factor": metrics.get(
                        "profit_factor", 0
                    ),
                    "return_pct": metrics.get(
                        "total_return_pct", 0
                    ),
                    "trades": metrics.get(
                        "num_trades", 0
                    ),
                }
            )

        except Exception:
            continue

    results.sort(
        key=lambda x: x["profit_factor"],
        reverse=True
    )

    return results