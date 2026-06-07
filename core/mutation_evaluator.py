# core/mutation_evaluator.py

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

            if df is None or df.empty:
                continue

            df_feat = apply_all_indicators(
                df,
                cfg
            )

            metrics, weaknesses, suggestions, trades_df = run_backtest_v2(
                df_feat,
                cfg
            )

            results.append({
                "variant": mutation["name"],
                "description": mutation.get("description", ""),
                "profit_factor": round(metrics.get("profit_factor", 0), 2),
                "return_pct": round(metrics.get("total_return_pct", 0), 2),
                "win_rate": round(metrics.get("win_rate_pct", 0), 2),
                "drawdown": round(metrics.get("max_drawdown_pct", 0), 2),
                "trades": int(metrics.get("num_trades", 0)),
            })

        except Exception as e:
            print(f"Mutation Error: {mutation.get('name')}: {e}")

    results.sort(
        key=lambda x: x["profit_factor"],
        reverse=True
    )

    return results
