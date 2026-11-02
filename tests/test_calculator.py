"""Calendar boundaries and countdown semantics."""
import importlib.util
from pathlib import Path
from datetime import date
import unittest

spec = importlib.util.spec_from_file_location(
    "calculator", Path(__file__).resolve().parents[1] / "custom_components/date_countdown/calculator.py")
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)
calculate = calculator.calculate

class CalendarTests(unittest.TestCase):
    def test_user_example(self):
        self.assertEqual(calculate(date(2026, 9, 2), 24, "months", date(2026, 11, 2)),
                         (date(2028, 9, 2), 670, 91.7))

    def test_month_end(self):
        self.assertEqual(calculate(date(2026, 1, 31), 1, "months", date(2026, 1, 31)),
                         (date(2026, 2, 28), 28, 100))

    def test_leap_year(self):
        self.assertEqual(calculate(date(2024, 2, 29), 1, "years", date(2025, 2, 28)),
                         (date(2025, 2, 28), 0, 0))

    def test_overdue(self):
        self.assertEqual(calculate(date(2026, 1, 1), 1, "days", date(2026, 1, 4)),
                         (date(2026, 1, 2), -2, 0))

    def test_future_start(self):
        self.assertEqual(calculate(date(2026, 2, 1), 10, "days", date(2026, 1, 1))[2], 100)

    def test_invalid(self):
        for amount, unit in [(0, "days"), (-1, "months"), (1, "seconds")]:
            with self.assertRaises(ValueError):
                calculate(date(2026, 1, 1), amount, unit, date(2026, 1, 1))

if __name__ == "__main__":
    unittest.main()
