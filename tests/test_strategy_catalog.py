import unittest
import yaml
from core.strategy_catalog import CATALOG, catalog_export, catalog_origin, load_template
from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.strategy_contract import contract_gate_issues


class StrategyCatalogTests(unittest.TestCase):
    def test_ten_unique_sourced_unvalidated_specifications(self):
        self.assertEqual(len(CATALOG), 10)
        self.assertEqual(len({x['id'] for x in CATALOG}), 10)
        for item in CATALOG:
            self.assertTrue(item['source_url'].startswith('https://'))
            self.assertTrue(item['rules'] and item['failure_modes'] and item['refinements'])
            self.assertEqual(catalog_export(item)['validation_status'], 'NOT TESTED')

    def test_supported_template_compiles_without_inferred_values(self):
        supported = [x for x in CATALOG if not x['implementation_gaps']]
        self.assertEqual(len(supported), 1)
        for item in supported:
            schema = build_strategy_from_text(item['prompt'])
            cfg = yaml.safe_load(compile_schema_to_yaml(schema, item['market'], item['timeframe']))
            self.assertEqual(contract_gate_issues(cfg, require_approval=False), [])
            rules = cfg['strategy_contract']['rules']
            self.assertTrue(any(r['component'] == 'ema_reclaim_entry' for r in rules))
            self.assertFalse(cfg['strategy_contract']['source'].get('assumptions'))

    def test_unsupported_templates_cannot_be_launched(self):
        for item in CATALOG:
            if item['implementation_gaps']:
                state = {'bt_result': 'old'}
                with self.assertRaises(ValueError):
                    load_template(state, item)
                self.assertEqual(state, {'bt_result': 'old'})

    def test_new_draft_clears_stale_approval_and_evidence(self):
        state = {'blueprint_approved': True, 'bt_result': 'old', 'approved_strategy_yaml': 'old'}
        load_template(state, CATALOG[0])
        self.assertFalse(state['blueprint_approved'])
        self.assertNotIn('bt_result', state)
        self.assertNotIn('approved_strategy_yaml', state)
        self.assertEqual(state['ai_text'], CATALOG[0]['prompt'])
        self.assertEqual(catalog_origin(state['ai_text'])['id'], 'VA-001')
        self.assertIsNone(catalog_origin('a different strategy'))
