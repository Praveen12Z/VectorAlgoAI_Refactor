from copy import deepcopy

from core.market_fit_analyzer import MARKETS
from core.data_loader import load_ohlcv
from core.indicators import apply_all_indicators
from core.backtester_adapter import run_backtest_v2


def run_evolution_lab(mutations, years=2):

    results = []

    for mutation in mutations:

        for market in MARKETS:

            try:

                cfg = deepcopy(
                    mutation["config"]
                )

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

                metrics, _, _, _ = (
                    run_backtest_v2(
                        df,
                        cfg
                    )
                )

                results.append(
                    {
                        "variant":
                            mutation["name"],

                        "market":
                            market,

                        "profit_factor":
                            round(
                                metrics.get(
                                    "profit_factor",
                                    0
                                ),
                                2
                            ),

                        "return_pct":
                            round(
                                metrics.get(
                                    "total_return_pct",
                                    0
                                ),
                                2
                            ),

                        "trades":
                            int(
                                metrics.get(
                                    "num_trades",
                                    0
                                )
                            ),
                    }
                )

            except Exception:
                pass

    results.sort(
        key=lambda x: (
            x["profit_factor"],
            x["return_pct"]
        ),
        reverse=True
    )

    return results[:10]
