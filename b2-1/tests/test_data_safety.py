"""손상·빈 저장 파일에서 데이터가 사라지지 않는지 확인한다.

검증 과정에서 실제로 발견된 유실 경로를 회귀 테스트로 고정한 것이다.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from budget_app.models import Query, StorageError, ValidationError
from budget_app.service.ledger import Ledger, open_ledger
from budget_app.service.porting import Porting
from budget_app.service.recurring import Recurring
from budget_app.service.reports import Reports
from budget_app.storage import DataDir


class SafetyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.data = DataDir(self.root / "data")
        self.data.ensure()
        self.addCleanup(self._tmp.cleanup)

    def ledger(self) -> Ledger:
        return Ledger(self.data)


class SeedingTest(SafetyTestCase):
    def test_corrupt_category_file_is_not_overwritten(self) -> None:
        # 읽을 수 있는 행이 없다고 기본값으로 덮어쓰면 원본이 사라진다.
        self.data.categories.path.write_text("broken\n", encoding="utf-8")
        self.data.ensure()
        self.assertEqual(self.data.categories.path.read_text(encoding="utf-8"), "broken\n")

    def test_deleting_every_category_does_not_resurrect_defaults(self) -> None:
        for name in list(self.ledger().categories()):
            self.ledger().remove_category(name)
        self.data.ensure()
        self.assertEqual(self.ledger().categories(), [])

    def test_seeds_only_on_first_creation(self) -> None:
        fresh = DataDir(self.root / "fresh")
        self.assertTrue(fresh.ensure())
        self.assertFalse(fresh.ensure())

    def test_read_only_commands_do_not_change_data(self) -> None:
        self.data.categories.path.write_text("broken\n", encoding="utf-8")
        before = self.data.categories.path.read_bytes()
        Porting(self.ledger()).backup()
        open_ledger(self.data.root)
        self.assertEqual(self.data.categories.path.read_bytes(), before)


class StrictRewriteTest(SafetyTestCase):
    """파일을 통째로 다시 쓰는 경로는 손상 행을 지우지 않고 멈춰야 한다."""

    def test_budget_set_aborts_on_corruption(self) -> None:
        self.data.budgets.path.write_text(
            '{"month": "2024-01", "amount": 100}\nbroken\n', encoding="utf-8"
        )
        before = self.data.budgets.path.read_text(encoding="utf-8")
        with self.assertRaises(StorageError):
            Reports(self.ledger()).set_budget("2024-02", 200)
        self.assertEqual(self.data.budgets.path.read_text(encoding="utf-8"), before)

    def test_recurring_remove_aborts_on_corruption(self) -> None:
        recurring = Recurring(self.ledger())
        rule = recurring.create(
            name="월세", day=25, type="expense", category="rent", amount=1000
        )
        with self.data.recurring.path.open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
        before = self.data.recurring.path.read_text(encoding="utf-8")
        with self.assertRaises(StorageError):
            Recurring(self.ledger()).remove(rule.id)
        self.assertEqual(self.data.recurring.path.read_text(encoding="utf-8"), before)

    def test_category_remove_aborts_on_corruption(self) -> None:
        with self.data.categories.path.open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
        before = self.data.categories.path.read_text(encoding="utf-8")
        with self.assertRaises(StorageError):
            self.ledger().remove_category("rent")
        self.assertEqual(self.data.categories.path.read_text(encoding="utf-8"), before)

    def test_reading_still_tolerates_corruption(self) -> None:
        with self.data.categories.path.open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
        ledger = self.ledger()
        self.assertIn("food", ledger.categories())
        self.assertTrue(ledger.warnings)


class ExportTargetTest(SafetyTestCase):
    def test_export_refuses_to_overwrite_a_store_file(self) -> None:
        self.ledger().create(
            date=date(2024, 1, 15), type="expense", category="food", amount=1000
        )
        before = self.data.transactions.path.read_bytes()
        with self.assertRaises(ValidationError):
            Porting(self.ledger()).export(
                Query.for_month("2024-01"), self.data.transactions.path
            )
        self.assertEqual(self.data.transactions.path.read_bytes(), before)

    def test_other_paths_are_allowed(self) -> None:
        out = self.root / "export.csv"
        Porting(self.ledger()).export(Query.for_month("2024-01"), out)
        self.assertTrue(out.exists())


class RecurringReferenceTest(SafetyTestCase):
    def test_category_used_by_a_rule_is_protected(self) -> None:
        Recurring(self.ledger()).create(
            name="월세", day=25, type="expense", category="rent", amount=1000
        )
        with self.assertRaises(ValidationError):
            self.ledger().remove_category("rent")
        self.assertIn("rent", self.ledger().categories())


class AtomicApplyTest(SafetyTestCase):
    def test_apply_writes_once(self) -> None:
        recurring = Recurring(self.ledger())
        recurring.create(name="월세", day=25, type="expense", category="rent", amount=1000)
        recurring.create(name="월급", day=25, type="income", category="salary", amount=2000)
        created = Recurring(self.ledger()).apply("2024-03")
        self.assertEqual(len(created), 2)
        self.assertEqual([tx.id for tx in created], ["TX-000001", "TX-000002"])
        self.assertEqual(len(self.ledger().search(Query(), 10)), 2)

    def test_apply_aborts_without_partial_write_when_store_is_corrupt(self) -> None:
        recurring = Recurring(self.ledger())
        recurring.create(name="월세", day=25, type="expense", category="rent", amount=1000)
        self.data.transactions.path.write_text("broken\n", encoding="utf-8")
        before = self.data.transactions.path.read_text(encoding="utf-8")
        with self.assertRaises(StorageError):
            Recurring(self.ledger()).apply("2024-03")
        self.assertEqual(self.data.transactions.path.read_text(encoding="utf-8"), before)


class CorruptionLineNumberTest(SafetyTestCase):
    def test_line_number_points_at_the_real_line(self) -> None:
        # 앞에 빈 줄과 깨진 줄이 있으면 세어 가며 매긴 번호는 어긋난다.
        self.data.transactions.path.write_text(
            "\n"
            "broken\n"
            '{"id": "TX-000001", "type": "expense", "date": "2024-01-15",'
            ' "amount": 1000, "category": "food"}\n'
            '{"id": "TX-000002", "type": "nope", "date": "2024-01-16",'
            ' "amount": 1000, "category": "food"}\n',
            encoding="utf-8",
        )
        ledger = self.ledger()
        rows = ledger.search(Query(), 10)
        self.assertEqual(len(rows), 1)
        self.assertIn("줄: 2, 4", ledger.warnings[0])


if __name__ == "__main__":
    unittest.main()
