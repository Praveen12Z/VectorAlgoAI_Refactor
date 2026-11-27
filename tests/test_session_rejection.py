import unittest

import pandas as pd
import yaml

from core.ai_strategy_builder import build_strategy_from_text
from core.backtester_adapter import ExecutionCostModel, run_backtest_v2
from core.indicators import apply_all_indicators
from core.research_contract import strategy_contract_issues
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.strategy_config import parse_strategy_yaml
from core.strategy_contract import approve_strategy_contract, require_approved_strategy_contract
from core.validation_engine import run_chronological_validation


BRIEF = (
    "I want to backtest a failed breakout on XAUUSD using 15-minute candles. "
    "Mark the high of the previous completed New York trading day. "
    "Between 09:30 and 12:00 New York time, if a candle trades above that high and closes back below it, "
    "enter short at the next candle's open, only if that open is before 12:00. "
    "Put the stop loss one minimum price increment above the signal candle's high and target 1.5R. "
    "Allow one trade per day. Close any remaining position at 16:00 New York time. "
    "Use a simulated account of $25,000 and risk 0.5% per trade."
)
NY = "America/New_York"


def bars_for_days(days):
    index = pd.DatetimeIndex([
        timestamp for day in days
        for timestamp in pd.date_range(f"{day} 09:30", periods=26, freq="15min", tz=NY)
    ])
    return pd.DataFrame({"open": 99.0, "high": 100.0, "low": 98.0, "close": 99.0}, index=index)


def strategy():
    raw = yaml.safe_load(compile_schema_to_yaml(build_strategy_from_text(BRIEF), "NAS100", "1h"))
    approved = approve_strategy_contract(raw, assumptions_accepted=True)
    require_approved_strategy_contract(approved)
    return parse_strategy_yaml(yaml.safe_dump(approved))


class SessionRejectionTests(unittest.TestCase):
    def test_compiles_the_requested_market_timeframe_and_direction(self):
        cfg = strategy()
        self.assertEqual((cfg.market, cfg.timeframe), ("XAUUSD", "15m"))
        self.assertEqual(cfg.raw["strategy_contract"]["identity"]["direction"], "short")
        self.assertEqual(cfg.raw["entry"]["long"], [])
        self.assertEqual(cfg.raw["indicators"], [])
        self.assertEqual(cfg.raw["session_rejection"]["buffer_points"], 0.1)

    def test_index_proxy_requires_an_explicit_stop_buffer(self):
        brief = BRIEF.replace("XAUUSD", "NAS100")
        raw = yaml.safe_load(compile_schema_to_yaml(build_strategy_from_text(brief)))
        self.assertFalse(raw["entry"]["short"])
        self.assertTrue(any("price points" in issue for issue in strategy_contract_issues(raw)))
        explicit = brief.replace("one minimum price increment", "0.25 price points")
        raw = yaml.safe_load(compile_schema_to_yaml(build_strategy_from_text(explicit)))
        self.assertFalse(strategy_contract_issues(raw))
        self.assertEqual(raw["session_rejection"]["buffer_points"], 0.25)

    def test_extra_short_rule_blocks_approval_without_falling_back_to_long(self):
        schema = build_strategy_from_text(BRIEF + " Skip major news.")
        raw = yaml.safe_load(compile_schema_to_yaml(schema))
        self.assertEqual(raw["strategy_contract"]["identity"]["direction"], "short")
        self.assertEqual(raw["entry"], {"long": [], "short": []})
        self.assertTrue(strategy_contract_issues(raw))

    def test_short_entry_stop_target_daily_limit_noon_and_session_close(self):
        df = bars_for_days(("2026-03-06", "2026-03-09", "2026-03-10", "2026-03-11"))
        df.loc["2026-03-09 09:30", "high"] = 101
        df.loc["2026-03-09 09:45", "low"] = 95
        df.loc["2026-03-09 10:15", "high"] = 102
        df.loc["2026-03-10 11:45", "high"] = 103  # A noon fill must be excluded.
        df.loc["2026-03-11 09:30", "high"] = 104
        cfg = strategy()
        metrics, _, _, trades = run_backtest_v2(apply_all_indicators(df, cfg), cfg)
        self.assertEqual(trades["direction"].tolist(), ["short", "short"])
        self.assertEqual(trades["entry_time"].tolist(), [
            pd.Timestamp("2026-03-09 09:45", tz=NY), pd.Timestamp("2026-03-11 09:45", tz=NY),
        ])
        self.assertEqual(trades["exit_reason"].tolist(), ["TP", "session_close"])
        self.assertEqual(trades.iloc[-1]["exit_time"], pd.Timestamp("2026-03-11 16:00", tz=NY))
        self.assertAlmostEqual(trades.iloc[0]["initial_stop"], 101.1)
        self.assertAlmostEqual(trades.iloc[0]["initial_target"], 95.85)
        self.assertEqual(metrics["signal_diagnostics"]["blocked_daily_trade_limit"], 1)

    def test_incomplete_prior_session_cannot_define_a_reference_high(self):
        df = bars_for_days(("2026-03-06", "2026-03-09", "2026-03-10"))
        df = df.drop(pd.Timestamp("2026-03-09 15:45", tz=NY))
        df.loc["2026-03-10 09:30", "high"] = 103
        _, _, _, trades = run_backtest_v2(df, strategy())
        self.assertTrue(trades.empty)

    def test_validation_split_starts_on_a_session_boundary(self):
        df = bars_for_days(("2026-03-06", "2026-03-09", "2026-03-10", "2026-03-11"))
        valid = run_chronological_validation(df, strategy(), ExecutionCostModel(), holdout_pct=35)
        self.assertEqual(valid["holdout"]["period"][0], pd.Timestamp("2026-03-10 09:30", tz=NY))
