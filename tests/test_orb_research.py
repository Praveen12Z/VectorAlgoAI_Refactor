import unittest
import pandas as pd
from core.orb_research import screen_opening_range, selection_record


def inputs(symbols=('AAA',)):
    dates = pd.bdate_range('2026-01-01',periods=17).strftime('%Y-%m-%d')
    daily = pd.DataFrame([dict(session=d,symbol=s,open=10,high=11,low=9,close=10,volume=2_000_000) for d in dates for s in symbols])
    opening = daily.copy()
    opening['volume']=1000
    opening['close']=10.5
    return daily,opening


class ORBResearchTests(unittest.TestCase):
    def test_current_and_future_daily_values_cannot_change_selection(self):
        d,o=inputs()
        expected=screen_opening_range(d,o)
        d.loc[d.session >= o.session.iloc[-2], ['high','volume']]=[10000,99999999]
        actual=screen_opening_range(d,o)
        pd.testing.assert_series_equal(expected.iloc[-2],actual.iloc[-2])
        self.assertTrue(expected.iloc[-1].selected)
        self.assertEqual(expected.iloc[-1].prior_atr14,2)
        self.assertEqual(expected.iloc[-1].planned_stop_distance,.2)

    def test_long_short_doji_and_price_filter(self):
        d,o=inputs(('LONG','SHORT','DOJI','CHEAP'))
        last=o.session.max()
        o.loc[(o.session==last)&(o.symbol=='SHORT'),'close']=9.5
        o.loc[(o.session==last)&(o.symbol=='DOJI'),'close']=10
        o.loc[(o.session==last)&(o.symbol=='CHEAP'),['open','low']]=[5,4]
        r=screen_opening_range(d,o).query('session == @last').set_index('symbol')
        self.assertEqual(r.loc['SHORT','direction'],'short')
        self.assertTrue(r.loc['LONG','selected'])
        self.assertFalse(r.loc['DOJI','selected'])
        self.assertFalse(r.loc['CHEAP','selected'])

    def test_ranking_and_history_gaps(self):
        d,o=inputs(tuple(f'S{i:02}' for i in range(21)))
        r=screen_opening_range(d,o);last=o.session.max()
        self.assertEqual(int(r.query('session == @last').selected.sum()),20)
        self.assertFalse(r.query('session == @last and symbol == "S20"').iloc[0].selected)
        d=d.drop(d[(d.symbol=='S00') & (d.session==d.session.iloc[21])].index)
        r=screen_opening_range(d,o)
        self.assertIn('Incomplete',r.query('session == @last and symbol == "S00"').iloc[0].reason)

    def test_zero_volume_duplicate_and_record_identity(self):
        d,o=inputs();o['volume']=0
        r=screen_opening_range(d,o)
        self.assertFalse(r.selected.any())
        with self.assertRaises(ValueError): screen_opening_range(pd.concat([d,d.iloc[:1]]),o)
        record=selection_record(b'daily',b'opening',r)
        self.assertEqual(record,selection_record(b'daily',b'opening',r))
        self.assertNotEqual(record['record_hash'],selection_record(b'changed',b'opening',r)['record_hash'])
