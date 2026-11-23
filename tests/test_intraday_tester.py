import json
import unittest

import pandas as pd

from core.intraday_tester import STARTERS, run_intraday_tester


class IntradayTesterTests(unittest.TestCase):
    def test_zero_trade_days_count_and_partial_week_is_excluded(self):
        days = pd.bdate_range("2026-08-03", periods=9)
        starts = pd.DatetimeIndex([
            stamp for day in days for stamp in pd.date_range(
                day.replace(hour=9, minute=30), periods=390, freq="min", tz="America/New_York"
            )
        ])
        price = 100 + 0.01 * (starts.hour * 60 + starts.minute)
        data = pd.DataFrame({"timestamp": starts, "open": price, "high": price,
                             "low": price, "close": price})
        cfd = next(s for s in STARTERS if s.id == "CFD-01")
        result = run_intraday_tester(data.to_csv(index=False).encode(), cfd,
                                     round_turn_cost=1, cfd_point_value=1)
        self.assertEqual(len(result["days"]), 9)
        self.assertEqual(result["periods"], 1)
        self.assertEqual(result["median_trades"], 0)
        self.assertEqual(result["cadence_status"], "Insufficient sample")
        self.assertFalse(result["weeks"][-1]["included_in_cadence"])
        self.assertEqual(result["trades"], [])
        self.assertEqual(len(json.loads(json.dumps(result))["weeks"]), 2)

    def test_futures_tick_grid_rejects_wrong_prices(self):
        future = next(s for s in STARTERS if s.id == "FUT-01")
        closes = pd.date_range("2026-08-03 09:31", periods=390, freq="min", tz="America/New_York")
        raw = "\n".join(f"{end.tz_convert('UTC'):%Y%m%d %H%M%S};100.1;100.1;100.1;100.1;1"
                        for end in closes).encode()
        with self.assertRaisesRegex(ValueError, "tick grid"):
            run_intraday_tester(raw, future, round_turn_cost=3)
