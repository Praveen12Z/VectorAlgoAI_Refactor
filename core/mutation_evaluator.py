from core.data_loader import load_ohlcv
from core.indicators import apply_all_indicators
from core.backtester_adapter import run_backtest_v2


def evaluate_mutations(mutations, years=2):

    results = []

    for mutation in mutations:

        try:

            cfg = mutation["config"]

            df = load_ohlcv(
                cfg.market,
                cfg.timeframe,
                years
            )

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
                    "name": mutation["name"],
                    "pf": round(
                        metrics.get(
                            "profit_factor",
                            0
                        ),
                        2
                    ),
                    "return_pct": round(
                        metrics.get(
                            "total_return_pct",
                            0
                        ),
                        2
                    ),
                    "trades": int(
                        metrics.get(
                            "num_trades",
                            0
                        )
                    ),
                }
            )

        except Exception as e:

            print(
                f"Mutation Error: {e}"
            )

    results.sort(
        key=lambda x: x["pf"],
        reverse=True
    )

    return results
