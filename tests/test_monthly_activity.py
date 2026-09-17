import unittest
import pandas as pd
from core.monthly_activity import monthly_activity


class MonthlyActivityTests(unittest.TestCase):
    def test_zero_trade_months_and_boundaries_remain_visible(self):
        rows = monthly_activity(pd.date_range('2026-01-10', '2026-04-10', freq='D'), pd.DataFrame())
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1]['entries'], 0)
        self.assertEqual(rows[1]['frequency_target'], 'Below 50')
        self.assertEqual(rows[0]['frequency_target'], 'Not assessed')

    def test_entry_counts_and_exit_pnl_use_distinct_local_months(self):
        index = pd.date_range('2026-01-01', '2026-04-01', freq='D', tz='America/New_York')
        trades = pd.DataFrame([{'entry_time': pd.Timestamp('2026-03-01 02:00', tz='UTC'),
            'exit_time': pd.Timestamp('2026-03-02', tz='UTC'), 'pnl': -10}] * 55)
        rows = monthly_activity(index, trades)
        self.assertEqual(rows[1]['entries'], 55)
        self.assertEqual(rows[1]['frequency_target'], '50–60')
        self.assertEqual(rows[2]['net_realized_pnl'], -550)

    def test_missing_month_is_not_scored_as_inactive_strategy(self):
        rows = monthly_activity(pd.to_datetime(['2026-01-01', '2026-03-01']), pd.DataFrame())
        self.assertEqual(rows[1]['coverage'], 'No bars')
        self.assertEqual(rows[1]['frequency_target'], 'Not assessed')
