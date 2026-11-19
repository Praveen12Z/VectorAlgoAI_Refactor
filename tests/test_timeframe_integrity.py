import unittest
from unittest.mock import patch
from core.data_loader import _yf_interval_for_timeframe, _safe_period, load_ohlcv


class TimeframeIntegrityTests(unittest.TestCase):
    def test_unsupported_frames_never_become_hourly(self):
        for frame in ('5m', '1m', 'nonsense'):
            with self.subTest(frame=frame):
                with self.assertRaisesRegex(ValueError, 'Unsupported timeframe'):
                    _yf_interval_for_timeframe(frame)
                with self.assertRaisesRegex(ValueError, 'Unsupported timeframe'):
                    _safe_period(frame, 2)

    def test_bad_timeframe_cache_cannot_be_reused(self):
        with patch('core.data_loader._read_cache') as cache:
            with self.assertRaisesRegex(ValueError, 'Unsupported timeframe'):
                load_ohlcv('NAS100', '5m')
            cache.assert_not_called()

    def test_supported_frames_and_aliases_unchanged(self):
        for frame, interval in [('15min','15m'), ('60m','1h'), ('4h','1h'), ('day','1d')]:
            self.assertEqual(_yf_interval_for_timeframe(frame), interval)

    def test_cache_keys_follow_the_actual_download_period(self):
        from core.data_loader import _cache_path

        def key(frame, years):
            return _cache_path("NAS100", frame, _safe_period(frame, years))

        self.assertNotEqual(key("1h", 1), key("1h", 2))
        self.assertEqual(key("1h", 2), key("1h", 15))
        self.assertNotEqual(key("1d", 2), key("1d", 15))
