"""반복 내역 테스트."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from budget_app.errors import NotFoundError, StorageError, ValidationError
from budget_app.models import Query
from budget_app.service.categories import Categories
from budget_app.service.ledger import Ledger
from budget_app.service.recurring import Recurring
from budget_app.storage import DataDir


class RecurringTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data = DataDir(Path(self._tmp.name) / "data")
        self.data.ensure()
        self.addCleanup(self._tmp.cleanup)

    def recurring(self) -> Recurring:
        return Recurring(Ledger(self.data))

    def rule(self, **over):
        params = dict(
            name="월세", day=25, type="expense", category="rent", amount=500_000
        )
        params.update(over)
        return self.recurring().create(**params)


class RuleTest(RecurringTestCase):
    def test_add_and_list(self) -> None:
        rule = self.rule()
        self.assertTrue(rule.id.startswith("RR-"))
        self.assertEqual([r.id for r in self.recurring().rules()], [rule.id])

    def test_category_must_exist(self) -> None:
        with self.assertRaises(NotFoundError):
            self.rule(category="nope")

    def test_invalid_day(self) -> None:
        with self.assertRaises(ValidationError):
            self.rule(day=32)

    def test_remove(self) -> None:
        rule = self.rule()
        self.recurring().remove(rule.id)
        self.assertEqual(self.recurring().rules(), [])

    def test_remove_missing(self) -> None:
        with self.assertRaises(NotFoundError):
            self.recurring().remove("RR-deadbeef")

    def test_ids_are_unique_per_rule(self) -> None:
        self.assertNotEqual(self.rule().id, self.rule(name="적금").id)


class ApplyTest(RecurringTestCase):
    def test_creates_transaction_with_source(self) -> None:
        rule = self.rule()
        created = self.recurring().apply("2024-03")
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].source, f"{rule.id}:2024-03")
        self.assertEqual(created[0].date, date(2024, 3, 25))

    def test_day_is_clamped_to_last_day(self) -> None:
        self.rule(day=31)
        created = self.recurring().apply("2024-02")
        self.assertEqual(created[0].date, date(2024, 2, 29))

    def test_second_apply_is_a_no_op(self) -> None:
        self.rule()
        self.assertEqual(len(self.recurring().apply("2024-03")), 1)
        self.assertEqual(self.recurring().apply("2024-03"), [])
        self.assertEqual(len(Ledger(self.data).search(Query(), 10)), 1)

    def test_other_months_are_independent(self) -> None:
        self.rule()
        self.recurring().apply("2024-03")
        self.assertEqual(len(self.recurring().apply("2024-04")), 1)

    def test_deleting_the_generated_transaction_allows_regeneration(self) -> None:
        # 출처가 사라지므로 다시 만들어진다. 의도된 동작이다.
        self.rule()
        created = self.recurring().apply("2024-03")
        Ledger(self.data).delete(created[0].id)
        self.assertEqual(len(self.recurring().apply("2024-03")), 1)

    def test_recreated_rule_does_not_collide_with_old_transactions(self) -> None:
        # 규칙 id 가 순번이면 삭제 후 재등록 시 번호가 재사용돼, 옛 거래의 출처와
        # 겹쳐 새 규칙 적용이 통째로 건너뛰어진다. uuid 라서 그런 일이 없다.
        first = self.rule()
        self.recurring().apply("2024-03")
        self.recurring().remove(first.id)

        second = self.rule(amount=600_000)
        self.assertNotEqual(first.id, second.id)
        created = self.recurring().apply("2024-03")
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].amount, 600_000)

    def test_category_used_by_a_rule_cannot_be_removed(self) -> None:
        self.rule(category="food")
        with self.assertRaises(ValidationError) as ctx:
            Categories(Ledger(self.data)).remove("food")
        self.assertIn("반복 규칙", ctx.exception.message)

    def test_missing_category_is_skipped_with_a_warning(self) -> None:
        # 파일을 직접 고쳐 카테고리가 사라진 경우에도 나머지 규칙까지 막지 않는다.
        self.rule(category="food")
        self.data.categories.write_all(
            row for row in self.data.categories.stream() if row.get("name") != "food"
        )
        recurring = self.recurring()
        self.assertEqual(recurring.apply("2024-03"), [])
        self.assertTrue(recurring.warnings)

    def test_duplicate_source_stops_the_run(self) -> None:
        rule = self.rule()
        ledger = Ledger(self.data)
        for _ in range(2):
            ledger.create(
                date=date(2024, 3, 25), type="expense", category="rent",
                amount=1, source=f"{rule.id}:2024-03",
            )
        with self.assertRaises(StorageError):
            self.recurring().apply("2024-03")

    def test_invalid_month(self) -> None:
        with self.assertRaises(ValidationError):
            self.recurring().apply("2024-13")

    def test_no_rules_creates_nothing(self) -> None:
        self.assertEqual(self.recurring().apply("2024-03"), [])


if __name__ == "__main__":
    unittest.main()
