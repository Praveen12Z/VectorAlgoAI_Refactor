import unittest
import pandas as pd
from core.backtester_adapter import ExecutionCostModel, run_backtest_v2
from core.strategy_config import parse_strategy_yaml
from test_execution_contract import BLUEPRINT


class NextOpenTests(unittest.TestCase):
    def run_rows(self, rows, blueprint=BLUEPRINT, costs=None):
        frame = pd.DataFrame(rows, columns=['open', 'high', 'low', 'close', 'atr'],
            index=pd.date_range('2026-01-01', periods=len(rows), freq='h'))
        return run_backtest_v2(frame, parse_strategy_yaml(blueprint), costs)

    def test_signal_bar_cannot_fill_and_entry_bar_atr_cannot_leak(self):
        metrics, _, _, trades = self.run_rows([
            [100, 130, 70, 100, 10], [110, 131, 105, 110, 999]])
        trade = trades.iloc[0]
        self.assertEqual(len(trades), 1)
        self.assertLess(trade.signal_time, trade.entry_time)
        self.assertEqual(trade.entry_price, 110)
        self.assertEqual(trade.initial_stop, 100)
        self.assertEqual(trade.initial_target, 130)
        self.assertEqual(trade.exit_reason, 'TP')
        self.assertAlmostEqual(trade['size'], 10)

    def test_final_bar_signal_is_not_filled_without_next_bar(self):
        _, _, _, trades = self.run_rows([[90, 91, 89, 90, 10], [90, 101, 89, 100, 10]])
        self.assertTrue(trades.empty)

    def test_entry_on_final_bar_is_closed_not_dropped(self):
        _, _, _, trades = self.run_rows([[100, 101, 99, 100, 10], [105, 107, 104, 106, 10]])
        self.assertEqual(trades.iloc[0].exit_reason, 'time_exit')
        self.assertEqual(trades.iloc[0].entry_price, 105)
        self.assertEqual(trades.iloc[0].exit_price, 106)

    def test_stop_gap_is_worse_than_planned_risk(self):
        metrics, _, _, trades = self.run_rows([
            [100, 101, 99, 100, 10], [100, 105, 95, 100, 10], [80, 85, 75, 80, 10]])
        self.assertEqual(trades.iloc[0].exit_price, 80)
        self.assertEqual(trades.iloc[0].pnl, -200)
        self.assertAlmostEqual(metrics['max_drawdown_pct'], -2)

    def test_target_at_open_precedes_later_stop_touch(self):
        _, _, _, trades = self.run_rows([
            [100, 101, 99, 100, 10], [100, 105, 95, 100, 10], [125, 130, 85, 100, 10]])
        self.assertEqual(trades.iloc[0].exit_reason, 'TP')
        self.assertEqual(trades.iloc[0].exit_price, 120)

    def test_drawdown_includes_unrealized_loss_and_initial_equity(self):
        metrics, _, _, trades = self.run_rows([
            [100, 101, 99, 100, 10], [100, 101, 91, 92, 10], [100, 121, 99, 120, 10]])
        self.assertAlmostEqual(metrics['max_drawdown_pct'], -.8)
        self.assertEqual(trades.iloc[0].pnl, 200)

    def test_short_stop_and_point_value_costs(self):
        config = BLUEPRINT.replace('  long:\n', '  swap:\n').replace('  short: []', '  long: []').replace('  swap:\n', '  short:\n').replace('point_value: 1', 'point_value: 2')
        _, _, _, trades = self.run_rows([[100, 101, 99, 100, 10], [105, 116, 80, 105, 99]],
            config, ExecutionCostModel(spread_points=1, commission_per_unit_round_turn=1))
        self.assertEqual(trades.iloc[0].direction, 'short')
        self.assertEqual(trades.iloc[0].exit_price, 115)
        self.assertAlmostEqual(trades.iloc[0]['size'], 100 / 23)
        self.assertAlmostEqual(trades.iloc[0].pnl, -100)

    def test_invalid_ohlc_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid OHLC'):
            self.run_rows([[100, 90, 95, 100, 10]])
