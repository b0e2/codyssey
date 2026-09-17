"""손상·빈 저장 파일에서 데이터가 사라지지 않는지 확인한다.

검증 과정에서 실제로 발견된 유실 경로를 회귀 테스트로 고정한 것이다.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import date
from unittest.mock import patch
from pathlib import Path

from budget_app.models import Query, StorageError, ValidationError
from budget_app.service.ledger import Ledger, open_ledger
from budget_app.service.porting import Porting
from budget_app.service.recurring import Recurring
from budget_app.service.reports import Reports
from budget_app.storage import DataDir, JsonlStore


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

    def test_reading_stops_on_corruption_too(self) -> None:
        # 조회와 쓰기가 같은 기준을 쓴다. 일부만 보여주는 상태가 없다.
        with self.data.categories.path.open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
        with self.assertRaises(StorageError):
            self.ledger().categories()


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


class RepairTest(SafetyTestCase):
    """복구는 지우지 않고 옮긴다."""

    def _break(self, store, text: str = "broken") -> None:
        with store.path.open("a", encoding="utf-8") as fp:
            fp.write(text + "\n")

    def test_moves_unreadable_rows_and_keeps_the_rest(self) -> None:
        self.ledger().create(
            date=date(2024, 1, 15), type="expense", category="food", amount=1000
        )
        self._break(self.data.transactions)
        report = Porting(self.ledger()).repair()

        self.assertEqual(report.moved, {"transactions.jsonl": 1})
        self.assertEqual(len(self.ledger().search(Query(), 10)), 1)
        quarantined = report.destination / "transactions.jsonl"
        self.assertEqual(quarantined.read_text(encoding="utf-8"), "broken\n")

    def test_rows_breaking_the_rules_are_moved_too(self) -> None:
        self.data.transactions.path.write_text(
            '{"id": "TX-000001", "type": "expense", "date": "2024-01-15",'
            ' "amount": 0, "category": "food"}\n',
            encoding="utf-8",
        )
        report = Porting(self.ledger()).repair()
        self.assertEqual(report.total, 1)
        self.assertEqual(list(self.data.transactions.stream()), [])

    def test_every_store_is_checked(self) -> None:
        for store in self.data.stores:
            self._break(store)
        report = Porting(self.ledger()).repair()
        self.assertEqual(len(report.moved), 4)

    def test_nothing_to_do(self) -> None:
        report = Porting(self.ledger()).repair()
        self.assertEqual(report.moved, {})
        self.assertIsNone(report.destination)

    def test_healthy_files_are_left_alone(self) -> None:
        before = self.data.categories.path.read_bytes()
        self._break(self.data.budgets)
        Porting(self.ledger()).repair()
        self.assertEqual(self.data.categories.path.read_bytes(), before)


class AppendPathStrictnessTest(SafetyTestCase):
    """덧붙이는 명령도 파일 전체를 다시 쓰므로 기존 행을 그대로 복사하면 안 된다."""

    def _store_with_semantic_corruption(self) -> str:
        self.data.transactions.path.write_text(
            '{"id": "TX-000001", "type": "expense", "date": "2024-01-15",'
            ' "amount": 0, "category": "food"}\n',
            encoding="utf-8",
        )
        return self.data.transactions.path.read_text(encoding="utf-8")

    def test_import_aborts(self) -> None:
        before = self._store_with_semantic_corruption()
        src = self.root / "in.csv"
        src.write_text(
            "date,type,category,amount,memo,tags\n2024-02-01,expense,food,1000,,\n",
            encoding="utf-8",
        )
        with self.assertRaises(StorageError):
            Porting(self.ledger()).import_csv(src)
        self.assertEqual(self.data.transactions.path.read_text(encoding="utf-8"), before)

    def test_recurring_apply_aborts(self) -> None:
        Recurring(self.ledger()).create(
            name="월세", day=25, type="expense", category="rent", amount=1000
        )
        before = self._store_with_semantic_corruption()
        with self.assertRaises(StorageError):
            Recurring(self.ledger()).apply("2024-03")
        self.assertEqual(self.data.transactions.path.read_text(encoding="utf-8"), before)


class ExportWriteFailureTest(SafetyTestCase):
    def test_replace_failure_is_a_storage_error(self) -> None:
        # 교체 단계만 가드 밖에 두면 그 실패가 내부 오류로 새어 나간다.
        out = self.root / "out.csv"
        with patch("budget_app.service.porting.os.replace", side_effect=OSError(13, "denied")):
            with self.assertRaises(StorageError):
                Porting(self.ledger()).export(Query.for_month("2024-01"), out)

    def test_no_temp_file_is_left_behind(self) -> None:
        out = self.root / "out.csv"
        with patch("budget_app.service.porting.os.replace", side_effect=OSError(13, "denied")):
            with self.assertRaises(StorageError):
                Porting(self.ledger()).export(Query.for_month("2024-01"), out)
        self.assertEqual([p for p in self.root.iterdir() if p.name.endswith(".tmp")], [])
