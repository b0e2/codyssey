"""거래 서비스 테스트."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from budget_app.models import (
    NotFoundError,
    Query,
    StorageError,
    ValidationError,
)
from budget_app.service.ledger import Ledger
from budget_app.storage import DataDir


class LedgerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data = DataDir(Path(self._tmp.name) / "data")
        self.data.ensure()
        self.addCleanup(self._tmp.cleanup)

    def ledger(self) -> Ledger:
        return Ledger(self.data)

    def add(self, day: str, amount: int = 1000, **over) -> None:
        params = dict(
            date=date.fromisoformat(day),
            type="expense",
            category="food",
            amount=amount,
        )
        params.update(over)
        self.ledger().create(**params)


class CategoryGateTest(LedgerTestCase):
    def test_seeded_categories_are_visible(self) -> None:
        self.assertIn("food", self.ledger().categories())

    def test_unknown_category_is_rejected(self) -> None:
        with self.assertRaises(NotFoundError):
            self.add("2024-01-15", category="unknown")

    def test_nothing_is_written_when_category_is_unknown(self) -> None:
        with self.assertRaises(NotFoundError):
            self.add("2024-01-15", category="unknown")
        self.assertEqual(list(self.data.transactions.stream()), [])


class NumberingTest(LedgerTestCase):
    def test_starts_at_one(self) -> None:
        self.assertEqual(self.ledger().next_id(), "TX-000001")

    def test_increments_from_last_row(self) -> None:
        self.add("2024-01-15")
        self.add("2024-01-16")
        self.assertEqual(self.ledger().next_id(), "TX-000003")

    def test_corrupt_last_id_stops_numbering(self) -> None:
        self.data.transactions.path.write_text(
            json.dumps({"id": "oops"}) + "\n", encoding="utf-8"
        )
        with self.assertRaises(StorageError):
            self.ledger().next_id()


class SearchTest(LedgerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.add("2024-01-10", 1000, memo="커피")
        self.add("2024-01-20", 2000, category="transport", tags=["Commute"])
        self.add("2024-01-05", 3000, type="income", category="salary")

    def test_newest_first_regardless_of_insertion_order(self) -> None:
        # 저장 순서와 날짜 순서가 다르다. 정렬 기준은 날짜다.
        rows = self.ledger().search(Query(), 10)
        self.assertEqual(
            [tx.date.isoformat() for tx in rows],
            ["2024-01-20", "2024-01-10", "2024-01-05"],
        )

    def test_same_date_breaks_tie_by_sequence(self) -> None:
        self.add("2024-02-01", 10)
        self.add("2024-02-01", 20)
        rows = self.ledger().search(Query.for_month("2024-02"), 10)
        self.assertEqual([tx.amount for tx in rows], [20, 10])

    def test_limit_applies(self) -> None:
        self.assertEqual(len(self.ledger().search(Query(), 2)), 2)

    def test_limit_must_be_positive(self) -> None:
        with self.assertRaises(ValidationError):
            self.ledger().search(Query(), 0)

    def test_filters(self) -> None:
        ledger = self.ledger()
        self.assertEqual(len(ledger.search(Query(type="income"), 10)), 1)
        self.assertEqual(len(ledger.search(Query(category="transport"), 10)), 1)
        self.assertEqual(len(ledger.search(Query(keyword="커피"), 10)), 1)
        self.assertEqual(len(ledger.search(Query(tag="commute"), 10)), 1)

    def test_date_range_is_inclusive(self) -> None:
        rows = self.ledger().search(
            Query(date_from=date(2024, 1, 10), date_to=date(2024, 1, 20)), 10
        )
        self.assertEqual(len(rows), 2)


class CorruptionTest(LedgerTestCase):
    def test_corrupt_rows_are_skipped_with_a_warning(self) -> None:
        self.add("2024-01-10")
        with self.data.transactions.path.open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
            fp.write(json.dumps({"id": "TX-000002", "type": "expense"}) + "\n")
        ledger = self.ledger()
        rows = ledger.search(Query(), 10)
        self.assertEqual(len(rows), 1)
        self.assertTrue(ledger.warnings)
        self.assertIn("건너뛰었습니다", ledger.warnings[0])

    def test_reading_never_fails_on_corruption(self) -> None:
        self.data.transactions.path.write_text("broken\n", encoding="utf-8")
        self.assertEqual(self.ledger().search(Query(), 10), [])


class GetTest(LedgerTestCase):
    def test_found(self) -> None:
        self.add("2024-01-10")
        self.assertEqual(self.ledger().get("TX-000001").amount, 1000)

    def test_missing_id(self) -> None:
        with self.assertRaises(NotFoundError):
            self.ledger().get("TX-000999")

    def test_malformed_id(self) -> None:
        with self.assertRaises(ValidationError):
            self.ledger().get("nope")


if __name__ == "__main__":
    unittest.main()
