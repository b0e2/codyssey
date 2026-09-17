"""월별 집계와 예산 테스트."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from budget_app.models import StorageError, ValidationError
from budget_app.service.ledger import Ledger
from budget_app.service.reports import Reports
from budget_app.storage import DataDir


class ReportsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data = DataDir(Path(self._tmp.name) / "data")
        self.data.ensure()
        self.addCleanup(self._tmp.cleanup)

    def reports(self) -> Reports:
        return Reports(Ledger(self.data))

    def add(self, day: str, amount: int, type: str = "expense", category: str = "food") -> None:
        Ledger(self.data).create(
            date=date.fromisoformat(day), type=type, category=category, amount=amount
        )


class SummaryTest(ReportsTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.add("2024-01-05", 150_000, category="rent")
        self.add("2024-01-15", 15_000)
        self.add("2024-01-20", 30_000)
        self.add("2024-01-12", 20_000, category="transport")
        self.add("2024-01-14", 3_000_000, type="income", category="salary")
        self.add("2024-02-01", 99_000)  # 다른 달

    def test_totals(self) -> None:
        summary = self.reports().summarize("2024-01")
        self.assertEqual(summary.total_income, 3_000_000)
        self.assertEqual(summary.total_expense, 215_000)
        self.assertEqual(summary.balance, 2_785_000)

    def test_other_months_are_excluded(self) -> None:
        self.assertEqual(self.reports().summarize("2024-02").total_expense, 99_000)

    def test_expense_is_grouped_by_category(self) -> None:
        summary = self.reports().summarize("2024-01")
        self.assertEqual(summary.expense_by_category["food"], 45_000)
        self.assertNotIn("salary", summary.expense_by_category)

    def test_top_expenses(self) -> None:
        summary = self.reports().summarize("2024-01")
        self.assertEqual(
            summary.top_expenses(3),
            [("rent", 150_000), ("food", 45_000), ("transport", 20_000)],
        )

    def test_month_without_data_is_empty_not_an_error(self) -> None:
        summary = self.reports().summarize("2024-05")
        self.assertTrue(summary.is_empty)
        self.assertEqual(summary.balance, 0)

    def test_invalid_month(self) -> None:
        with self.assertRaises(ValidationError):
            self.reports().summarize("2024-13")


class BudgetTest(ReportsTestCase):
    def test_unset_budget_is_none(self) -> None:
        self.assertIsNone(self.reports().budget_for("2024-01"))
        self.assertIsNone(self.reports().summarize("2024-01").usage_rate)

    def test_set_and_read(self) -> None:
        self.reports().set_budget("2024-01", 500_000)
        self.assertEqual(self.reports().budget_for("2024-01"), 500_000)

    def test_setting_twice_replaces_instead_of_appending(self) -> None:
        # 같은 달이 여러 줄 쌓이면 어느 값이 맞는지 알 수 없다.
        self.reports().set_budget("2024-01", 500_000)
        self.reports().set_budget("2024-01", 300_000)
        rows = list(self.data.budgets.stream())
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.reports().budget_for("2024-01"), 300_000)

    def test_budgets_are_sorted_by_month(self) -> None:
        self.reports().set_budget("2024-03", 3)
        self.reports().set_budget("2024-01", 1)
        self.reports().set_budget("2024-02", 2)
        self.assertEqual([b.month for b in self.reports().budgets()], ["2024-01", "2024-02", "2024-03"])

    def test_invalid_amount(self) -> None:
        with self.assertRaises(ValidationError):
            self.reports().set_budget("2024-01", 0)

    def test_unreadable_budget_row_stops_the_query(self) -> None:
        self.reports().set_budget("2024-01", 500_000)
        with self.data.budgets.path.open("a", encoding="utf-8") as fp:
            fp.write('{"month": "nope"}\n')
        with self.assertRaises(StorageError):
            self.reports().budget_for("2024-01")

    def test_summary_carries_budget_state(self) -> None:
        self.add("2024-01-15", 215_000)
        self.reports().set_budget("2024-01", 500_000)
        summary = self.reports().summarize("2024-01")
        self.assertAlmostEqual(summary.usage_rate, 43.0)
        self.assertFalse(summary.is_over_budget)

    def test_over_budget(self) -> None:
        self.add("2024-01-15", 215_000)
        self.reports().set_budget("2024-01", 200_000)
        self.assertTrue(self.reports().summarize("2024-01").is_over_budget)

    def test_exactly_on_budget_is_not_over(self) -> None:
        self.add("2024-01-15", 200_000)
        self.reports().set_budget("2024-01", 200_000)
        summary = self.reports().summarize("2024-01")
        self.assertFalse(summary.is_over_budget)
        self.assertAlmostEqual(summary.usage_rate, 100.0)


if __name__ == "__main__":
    unittest.main()
