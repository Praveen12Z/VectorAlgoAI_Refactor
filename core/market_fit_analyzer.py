# core/market_fit_analyzer.py

from copy import deepcopy

from core.evidence_policy import MIN_SCORABLE_TRADES, evidence_is_sufficient


MARKETS = [
    "XAUUSD",
    # "EURUSD",
    # "GBPUSD",
    "USDJPY",
    # "AUDUSD",
    "NAS100",
    "US30",
    "BTCUSD",
    "ETHUSD",
]


def analyze_market_fit(cfg, years=2, baseline_metrics=None):

    if not evidence_is_sufficient(baseline_metrics):
        return []

    # Expensive data/execution dependencies are intentionally loaded only after
    # the shared evidence gate permits a cross-market experiment.
    from core.backtester_adapter import run_backtest_v2
    from core.data_loader import load_ohlcv
    from core.indicators import apply_all_indicators

    results = []

    for market in MARKETS:

        try:

            local_cfg = deepcopy(cfg)
            local_cfg.market = market

            df = load_ohlcv(
                market,
                local_cfg.timeframe,
                years
            )

            if df is None or df.empty:
                continue

            df = apply_all_indicators(
                df,
                local_cfg
            )

            metrics, weaknesses, suggestions, trades_df = (
                run_backtest_v2(
                    df,
                    local_cfg
                )
            )

            pf = metrics.get(
                "profit_factor",
                0
            )

            total_return = float(metrics.get("total_return_pct", 0))

            trades = int(
                metrics.get(
                    "num_trades",
                    0
                )
            )

            # ---------------------------------
            # Ignore statistically useless runs
            # ---------------------------------
            if trades < MIN_SCORABLE_TRADES or float(pf) < 1.10 or total_return <= 0:
                continue

            confidence_score = (
                pf *
                min(trades / 30, 1.0)
            )

            results.append(
                {
                    "market": market,
                    "profit_factor": round(
                        pf,
                        2
                    ),
                    "return_pct": round(
                            total_return,
                        2
                    ),
                    "trades": trades,
                    "confidence_score": round(
                        confidence_score,
                        2
                    ),
                }
            )

        except Exception as e:

            print(
                f"Market Fit Error {market}: {e}"
            )

    results.sort(
        key=lambda x: x[
            "confidence_score"
        ],
        reverse=True
    )

    return results
