import unittest
from datetime import date

from app.summary import fill_days, manila_bounds, summarize, valid_username, validate_range


class SummaryTests(unittest.TestCase):
    def test_range_ok(self):
        self.assertEqual(validate_range("2026-10-01", "2026-10-07"), (date(2026, 10, 1), date(2026, 10, 7)))

    def test_range_end_before_start(self):
        with self.assertRaises(ValueError):
            validate_range("2026-10-07", "2026-10-01")

    def test_range_bad_date(self):
        with self.assertRaises(ValueError):
            validate_range("10/01/2026", "2026-10-07")

    def test_range_too_long(self):
        with self.assertRaises(ValueError):
            validate_range("2024-01-01", "2026-01-01")

    def test_fill_days_adds_zero_days(self):
        rows = [{"day": "2026-10-02", "peak_inside": 12, "total_in": 40, "total_out": 35}]
        days = fill_days(rows, date(2026, 10, 1), date(2026, 10, 3))
        self.assertEqual([d["day"] for d in days], ["2026-10-01", "2026-10-02", "2026-10-03"])
        self.assertEqual([d["has_data"] for d in days], [False, True, False])
        self.assertEqual(days[0]["peak_inside"], 0)

    def test_summarize(self):
        rows = [
            {"day": "2026-10-01", "peak_inside": 10, "total_in": 30, "total_out": 28},
            {"day": "2026-10-02", "peak_inside": 31, "total_in": 80, "total_out": 70},
        ]
        s = summarize(fill_days(rows, date(2026, 10, 1), date(2026, 10, 3)))
        self.assertEqual(s["total_in"], 110)
        self.assertEqual(s["total_out"], 98)
        self.assertEqual(s["peak_inside"], 31)
        self.assertEqual(s["busiest_day"], "2026-10-02")
        self.assertEqual((s["days_with_data"], s["days_in_range"]), (2, 3))

    def test_summarize_no_data(self):
        s = summarize(fill_days([], date(2026, 10, 1), date(2026, 10, 2)))
        self.assertEqual(s["peak_inside"], 0)
        self.assertIsNone(s["busiest_day"])

    def test_manila_bounds_cover_whole_days(self):
        lo, hi = manila_bounds(date(2026, 10, 1), date(2026, 10, 1))
        self.assertEqual(lo, "2026-10-01T00:00:00+08:00")
        self.assertEqual(hi, "2026-10-02T00:00:00+08:00")

    def test_username_rules(self):
        self.assertTrue(valid_username("maria.cruz_1"))
        for bad in ("ab", "Has Space", "UPPER", "a" * 31, "semi;colon", "emojié"):
            self.assertFalse(valid_username(bad), bad)


if __name__ == "__main__":
    unittest.main()
