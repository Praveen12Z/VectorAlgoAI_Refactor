import unittest
import pandas as pd
from core.backtester_adapter import run_backtest_v2
from core.strategy_config import parse_strategy_yaml
from test_execution_contract import BLUEPRINT


class SignalDiagnosticsTests(unittest.TestCase):
    def test_counts_reconcile_with_blocked_entries_and_final_bar(self):
        frame = pd.DataFrame({'open':[100]*4, 'high':[101]*4,
                              'low':[99]*4, 'close':[100]*4, 'atr':[10]*4},
                             index=pd.date_range('2026-01-01', periods=4, freq='h'))
        metrics, _, _, trades = run_backtest_v2(frame, parse_strategy_yaml(BLUEPRINT))
        d = metrics['signal_diagnostics']
        self.assertEqual(d['signal_bars_with_next_open'], 3)
        self.assertEqual(d['qualifying_signal_bars'], 3)
        self.assertEqual(d['blocked_open_position'], 2)
        self.assertEqual(d['entries_executed'], len(trades))
        self.assertEqual(d['entries_executed'], 1)
        self.assertEqual(d['final_bar_signal_without_next_open'], 1)
        self.assertEqual(d['qualifying_signal_bars'], d['entries_executed'] + d['blocked_open_position'] + d['blocked_nonpositive_equity'])

    def test_rule_counts_distinguish_individual_from_combined_passes(self):
        config = BLUEPRINT.replace('      right: 99', '      right: 99\n    - left: atr\n      op: ">"\n      right: 5')
        frame = pd.DataFrame({'open':[98,100,100], 'high':[101]*3, 'low':[97]*3,
                              'close':[98,100,100], 'atr':[10,2,10]},
                             index=pd.date_range('2026-01-01', periods=3, freq='h'))
        metrics, _, _, trades = run_backtest_v2(frame, parse_strategy_yaml(config))
        d = metrics['signal_diagnostics']
        self.assertTrue(trades.empty)
        self.assertEqual([r['passed_alone'] for r in d['rules']], [1,1])
        self.assertEqual([r['passed_cumulatively'] for r in d['rules']], [1,0])
        self.assertEqual(d['qualifying_signal_bars'], 0)
        self.assertEqual(d['final_bar_signal_without_next_open'], 1)
