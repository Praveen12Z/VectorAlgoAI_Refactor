import unittest
import pandas as pd
import yaml
from core.backtester_adapter import run_backtest_v2
from core.indicators import apply_all_indicators
from core.strategy_config import parse_strategy_yaml
from core.strategy_catalog import CATALOG, catalog_export, catalog_origin, load_template
from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.strategy_contract import contract_gate_issues


class StrategyCatalogTests(unittest.TestCase):
    def test_unique_sourced_unvalidated_specifications(self):
        self.assertEqual(len(CATALOG), 12)
        self.assertEqual(len({x['id'] for x in CATALOG}), 12)
        for item in CATALOG:
            self.assertTrue(item['source_url'].startswith('https://'))
            self.assertTrue(item['rules'] and item['failure_modes'] and item['refinements'])
            self.assertEqual(catalog_export(item)['validation_status'], 'NOT TESTED')

    def test_supported_template_compiles_without_inferred_values(self):
        supported = [x for x in CATALOG if not x['implementation_gaps']]
        self.assertEqual({x["id"] for x in supported}, {"VA-001", "VA-002", "VA-003", "VA-004", "VA-006", "VA-008"})
        for item in supported:
            schema = build_strategy_from_text(item['prompt'])
            cfg = yaml.safe_load(compile_schema_to_yaml(schema, item['market'], item['timeframe']))
            self.assertEqual(contract_gate_issues(cfg, require_approval=False), [])
            rules = cfg['strategy_contract']['rules']
            triggers = {"VA-001": "ema_reclaim_entry", "VA-002": "channel_breakout",
                        "VA-003": "rsi_pullback", "VA-004": "bollinger_squeeze",
                        "VA-006": "resistance_retest", "VA-008": "demand_zone_retest"}
            self.assertTrue(any(r['component'] == triggers[item['id']] for r in rules))
            if item['id'] != 'VA-003':
                self.assertFalse(cfg['strategy_contract']['source'].get('assumptions'))

    def test_research_specifications_open_with_rules_and_clear_stale_approval(self):
        for item in CATALOG:
            if item['implementation_gaps']:
                with self.subTest(strategy=item['id']):
                    state = {'bt_result': 'old', 'blueprint_approved': True}
                    load_template(state, item)
                    self.assertEqual(state['active_workspace_stage'], 'thesis')
                    self.assertEqual(state['catalog_specification']['rules'], item['rules'])
                    self.assertEqual(state['catalog_specification']['market'], item['market'])
                    self.assertNotIn('bt_result', state)
                    self.assertFalse(state['blueprint_approved'])

    def test_new_draft_clears_stale_approval_and_evidence(self):
        state = {'blueprint_approved': True, 'bt_result': 'old', 'approved_strategy_yaml': 'old',
                 'catalog_specification': catalog_export(CATALOG[-1])}
        load_template(state, CATALOG[0])
        self.assertFalse(state['blueprint_approved'])
        self.assertNotIn('bt_result', state)
        self.assertNotIn('approved_strategy_yaml', state)
        self.assertNotIn('catalog_specification', state)
        self.assertEqual(state['ai_text'], CATALOG[0]['prompt'])
        self.assertEqual(catalog_origin(state['ai_text'])['id'], 'VA-001')
        self.assertIsNone(catalog_origin('a different strategy'))

    def test_catalog_models_execute_on_completed_bars(self):
        scenarios = {
            "VA-002": ([100] * 20 + [110, 111, 112], 20),
            "VA-003": ([100 + i * 0.1 for i in range(210)] + [118, 116, 115, 117, 119, 120], 210),
            "VA-004": ([100] * 139 + [110, 111, 112], 139),
        }
        for strategy_id, (closes, signal_bar) in scenarios.items():
            with self.subTest(strategy=strategy_id):
                item = next(item for item in CATALOG if item["id"] == strategy_id)
                schema = build_strategy_from_text(item["prompt"])
                cfg = parse_strategy_yaml(compile_schema_to_yaml(schema, item["market"], item["timeframe"]))
                index = pd.date_range("2024-01-01", periods=len(closes), freq="h")
                bars = pd.DataFrame({
                    "open": closes, "high": [price + 1 for price in closes],
                    "low": [price - 1 for price in closes], "close": closes, "volume": 100,
                }, index=index)
                features = apply_all_indicators(bars, cfg)
                metrics, _, _, trades = run_backtest_v2(features, cfg)
                self.assertEqual(metrics["num_trades"], len(trades))
                self.assertGreater(len(trades), 0)
                first = trades.iloc[0]
                self.assertEqual(first["signal_time"], index[signal_bar])
                self.assertEqual(first["entry_time"], index[signal_bar + 1])
                stop_multiple = 1.5 if strategy_id == "VA-004" else 2
                stop = closes[signal_bar] - stop_multiple * features["wilder_atr"].iloc[signal_bar]
                self.assertAlmostEqual(first["initial_stop"], stop)
                if strategy_id == "VA-003":
                    self.assertEqual(first["exit_reason"], "indicator_exit")
                    self.assertEqual(first["exit_time"], index[215])
                else:
                    rr = 3 if strategy_id == "VA-002" else 2
                    fill = closes[signal_bar + 1]
                    self.assertAlmostEqual(first["initial_target"], fill + rr * (fill - stop))

    def test_retests_save_the_confirmed_level_and_fill_after_the_signal(self):
        for strategy_id in ("VA-006", "VA-008"):
            with self.subTest(strategy=strategy_id):
                item = next(item for item in CATALOG if item["id"] == strategy_id)
                schema = build_strategy_from_text(item["prompt"])
                cfg = parse_strategy_yaml(compile_schema_to_yaml(schema, item["market"], item["timeframe"]))
                bars = [[100, 102, 98, 100]] * 16
                if strategy_id == "VA-006":
                    bars += [[102, 105, 101, 103], [100, 102, 98, 100], [100, 102, 98, 100],
                             [106, 107, 105, 106], [106, 107, 105, 106], [106, 108, 105, 107]]
                    level, signal = 105, 20
                else:
                    bars += [[100, 101, 99, 100]] * 3
                    bars += [[106, 109, 105, 108], [104, 107, 100, 105], [106, 108, 104, 107]]
                    level, signal = 101, 20
                frame = pd.DataFrame(bars, columns=["open", "high", "low", "close"],
                                     index=pd.date_range("2024-01-01", periods=len(bars), freq="h"))
                features = apply_all_indicators(frame, cfg)
                prefix = apply_all_indicators(frame.iloc[:signal], cfg)
                column = "resistance_retest" if strategy_id == "VA-006" else "demand_zone_retest"
                pd.testing.assert_series_equal(features[column].iloc[:signal], prefix[column])
                _, _, _, ledger = run_backtest_v2(features, cfg)
                self.assertEqual(len(ledger), 1)
                trade = ledger.iloc[0]
                self.assertEqual(trade["setup_level"], level)
                self.assertEqual(trade["signal_time"], frame.index[signal])
                self.assertEqual(trade["entry_time"], frame.index[signal + 1])
                self.assertAlmostEqual(trade["initial_target"],
                                       trade["entry_price"] + 2 * trade["stop_distance"])
