import copy
import unittest
from core.experiment_tracking import annotate, comparison, metadata


class ExperimentTrackingTests(unittest.TestCase):
    def test_review_preserves_evidence_and_does_not_mutate_original(self):
        original = {'id': 'server-id', 'user_id': 'owner', 'created_at': 'today',
            'record_hash': 'original', 'validation_passed': False,
            'validation_status': 'INSUFFICIENT', 'strategy_yaml': 'rules',
            'trade_records': [{'pnl': -5}], 'full_metrics': {'profit_factor': .8},
            'execution_assumptions': {'cost_model': {'spread': 1}}}
        snapshot = copy.deepcopy(original)
        review = annotate(original, version='C', hypothesis='Test reclaim',
            decision='Rejected for deployment', notes='Hold-out adverse', review=True)
        self.assertEqual(original, snapshot)
        for key in ('validation_passed', 'validation_status', 'strategy_yaml', 'trade_records', 'full_metrics'):
            self.assertEqual(review[key], original[key])
        self.assertEqual(review['execution_assumptions']['cost_model'], {'spread': 1})
        self.assertEqual(metadata(review)['review_of_record_hash'], 'original')
        self.assertNotEqual(review['record_hash'], original['record_hash'])
        self.assertFalse({'id', 'user_id', 'created_at'} & review.keys())

    def test_deterministic_metadata_and_invalid_decision(self):
        record = {'execution_assumptions': {}}
        a = annotate(record, version='A', hypothesis='Test')
        self.assertEqual(a, annotate(record, version='A', hypothesis='Test'))
        self.assertNotEqual(a['record_hash'], annotate(record, version='B', hypothesis='Test')['record_hash'])
        with self.assertRaises(ValueError):
            annotate(record, version='A', hypothesis='', decision='Capital approved')

    def test_legacy_records_and_comparison(self):
        self.assertEqual(metadata({}), {})
        a = {'full_metrics': {'profit_factor': 1.1}, 'execution_assumptions': {'cost_model': {'spread': 1}}}
        b = {'full_metrics': {'profit_factor': .8}, 'execution_assumptions': {'cost_model': {'spread': 2}}}
        rows = {r['Field']: r for r in comparison(a, b)}
        self.assertEqual(rows['full_metrics: profit_factor']['B'], .8)
        self.assertNotEqual(rows['cost_model']['A'], rows['cost_model']['B'])
