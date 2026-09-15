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


class UpdateTest(LedgerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.add("2024-01-10", 1000, memo="커피", tags=["cafe"])
        self.add("2024-01-11", 2000)

    def test_single_field(self) -> None:
        tx = self.ledger().update("TX-000001", {"amount": 5000})
        self.assertEqual(tx.amount, 5000)
        self.assertEqual(self.ledger().get("TX-000001").memo, "커피")

    def test_empty_string_clears_memo_and_tags(self) -> None:
        self.ledger().update("TX-000001", {"memo": "", "tags": []})
        tx = self.ledger().get("TX-000001")
        self.assertEqual(tx.memo, "")
        self.assertEqual(tx.tags, [])

    def test_other_rows_are_untouched(self) -> None:
        self.ledger().update("TX-000001", {"amount": 5000})
        self.assertEqual(self.ledger().get("TX-000002").amount, 2000)
        self.assertEqual(len(self.ledger().search(Query(), 10)), 2)

    def test_missing_id(self) -> None:
        with self.assertRaises(NotFoundError):
            self.ledger().update("TX-000999", {"amount": 1})

    def test_empty_change_set(self) -> None:
        with self.assertRaises(ValidationError):
            self.ledger().update("TX-000001", {})

    def test_unknown_category(self) -> None:
        with self.assertRaises(NotFoundError):
            self.ledger().update("TX-000001", {"category": "nope"})

    def test_invalid_value_is_rejected_by_the_model(self) -> None:
        with self.assertRaises(ValidationError):
            self.ledger().update("TX-000001", {"amount": 0})

    def test_corrupt_file_aborts_and_preserves_original(self) -> None:
        path = self.data.transactions.path
        with path.open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
        before = path.read_text(encoding="utf-8")
        with self.assertRaises(StorageError):
            self.ledger().update("TX-000001", {"amount": 5000})
        self.assertEqual(path.read_text(encoding="utf-8"), before)


class DeleteTest(LedgerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.add("2024-01-10", 1000)
        self.add("2024-01-11", 2000)

    def test_removes_only_the_target(self) -> None:
        removed = self.ledger().delete("TX-000001")
        self.assertEqual(removed.amount, 1000)
        remaining = self.ledger().search(Query(), 10)
        self.assertEqual([tx.id for tx in remaining], ["TX-000002"])

    def test_missing_id(self) -> None:
        with self.assertRaises(NotFoundError):
            self.ledger().delete("TX-000999")

    def test_numbering_continues_after_deleting_the_last_row(self) -> None:
        # 마지막 행에서 채번하므로 번호가 재사용된다. 의도된 한계이며 문서에 적는다.
        self.ledger().delete("TX-000002")
        self.assertEqual(self.ledger().next_id(), "TX-000002")


class CategoryManagementTest(LedgerTestCase):
    def test_add_and_normalize(self) -> None:
        self.assertEqual(self.ledger().add_category("  hobby "), "hobby")
        self.assertIn("hobby", self.ledger().categories())

    def test_duplicate_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.ledger().add_category("food")

    def test_remove_unused(self) -> None:
        moved = self.ledger().remove_category("rent")
        self.assertEqual(moved, 0)
        self.assertNotIn("rent", self.ledger().categories())

    def test_remove_unknown(self) -> None:
        with self.assertRaises(NotFoundError):
            self.ledger().remove_category("nope")

    def test_remove_in_use_requires_replacement(self) -> None:
        self.add("2024-01-10")
        with self.assertRaises(ValidationError) as ctx:
            self.ledger().remove_category("food")
        self.assertIn("1건", ctx.exception.message)
        self.assertIn("food", self.ledger().categories())

    def test_remove_in_use_moves_transactions(self) -> None:
        self.add("2024-01-10")
        self.add("2024-01-11")
        moved = self.ledger().remove_category("food", "etc")
        self.assertEqual(moved, 2)
        self.assertNotIn("food", self.ledger().categories())
        self.assertEqual(
            {tx.category for tx in self.ledger().search(Query(), 10)}, {"etc"}
        )

    def test_replacement_must_exist(self) -> None:
        self.add("2024-01-10")
        with self.assertRaises(NotFoundError):
            self.ledger().remove_category("food", "nope")

    def test_replacement_cannot_be_itself(self) -> None:
        self.add("2024-01-10")
        with self.assertRaises(ValidationError):
            self.ledger().remove_category("food", "food")

    def test_transactions_are_committed_before_category_is_dropped(self) -> None:
        # 참조를 없앨 때는 참조하는 쪽을 먼저 바꾼다. 중간에 실패해도
        # 등록되지 않은 카테고리를 가리키는 거래가 생기지 않는다.
        self.add("2024-01-10")
        self.ledger().remove_category("food", "etc")
        categories = self.ledger().categories()
        for tx in self.ledger().search(Query(), 10):
            self.assertIn(tx.category, categories)
