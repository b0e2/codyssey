"""도메인 모델과 검증 규칙 테스트."""

from __future__ import annotations

import unittest
from datetime import date

from budget_app.errors import StorageError, ValidationError
from budget_app.validators import (
    clamp_day,
    format_tx_id,
    month_range,
    new_rule_id,
    normalize_category,
    parse_amount,
    parse_date,
    parse_month,
    parse_tags,
    parse_type,
)
from budget_app.models import Budget, MonthlySummary, Query, RecurringRule, Transaction


class ParseDateTest(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(parse_date("2024-01-15"), date(2024, 1, 15))

    def test_impossible_date(self) -> None:
        with self.assertRaises(ValidationError):
            parse_date("2024-13-40")

    def test_unpadded_is_rejected(self) -> None:
        # strptime 은 통과시키지만 저장 형식이 흔들리므로 막는다.
        with self.assertRaises(ValidationError):
            parse_date("2024-1-5")

    def test_empty(self) -> None:
        with self.assertRaises(ValidationError):
            parse_date("")


class ParseAmountTest(unittest.TestCase):
    def test_positive(self) -> None:
        self.assertEqual(parse_amount("15000"), 15000)

    def test_zero_and_negative(self) -> None:
        for bad in ("0", "-1", -5, 0):
            with self.subTest(value=bad), self.assertRaises(ValidationError):
                parse_amount(bad)

    def test_non_integer(self) -> None:
        for bad in ("abc", "1.5", "", True):
            with self.subTest(value=bad), self.assertRaises(ValidationError):
                parse_amount(bad)


class CategoryAndTagTest(unittest.TestCase):
    def test_empty_category(self) -> None:
        for bad in ("", "   "):
            with self.subTest(value=bad), self.assertRaises(ValidationError):
                normalize_category(bad)

    def test_comma_rejected(self) -> None:
        # CSV 의 tags 구분자와 충돌하므로 카테고리명에 쉼표를 허용하지 않는다.
        with self.assertRaises(ValidationError):
            normalize_category("food,drink")

    def test_too_long(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_category("x" * 33)

    def test_case_is_preserved(self) -> None:
        self.assertEqual(normalize_category("  Food "), "Food")

    def test_tags_drop_blanks_and_duplicates(self) -> None:
        self.assertEqual(parse_tags("meal, lunch, ,meal"), ["meal", "lunch"])

    def test_tags_none(self) -> None:
        self.assertEqual(parse_tags(None), [])


class TypeTest(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(parse_type("expense"), "expense")

    def test_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            parse_type("spending")


class MonthHelperTest(unittest.TestCase):
    def test_month_format(self) -> None:
        self.assertEqual(parse_month("2024-01"), "2024-01")
        for bad in ("2024-1", "2024-13", "2024/01", ""):
            with self.subTest(value=bad), self.assertRaises(ValidationError):
                parse_month(bad)

    def test_month_range(self) -> None:
        self.assertEqual(month_range("2024-02"), (date(2024, 2, 1), date(2024, 2, 29)))

    def test_clamp_day_to_last_day(self) -> None:
        # 31일 규칙은 그 달의 말일로 보정한다.
        self.assertEqual(clamp_day("2024-02", 31), date(2024, 2, 29))
        self.assertEqual(clamp_day("2023-02", 31), date(2023, 2, 28))
        self.assertEqual(clamp_day("2024-03", 25), date(2024, 3, 25))


class IdTest(unittest.TestCase):
    def test_format_and_limit(self) -> None:
        self.assertEqual(format_tx_id(12), "TX-000012")
        self.assertEqual(format_tx_id(999_999), "TX-999999")
        with self.assertRaises(StorageError):
            format_tx_id(1_000_000)

    def test_rule_id_is_not_sequential(self) -> None:
        # 규칙 id 가 재사용되면 옛 거래의 source 와 충돌한다.
        self.assertNotEqual(new_rule_id(), new_rule_id())


class TransactionTest(unittest.TestCase):
    def _tx(self, **over: object) -> Transaction:
        base = dict(
            id="TX-000012",
            type="expense",
            date=date(2024, 1, 15),
            amount=15000,
            category="food",
            memo="점심",
            tags=["meal"],
        )
        base.update(over)
        return Transaction(**base)  # type: ignore[arg-type]

    def test_invariants(self) -> None:
        for field, bad in (
            ("id", "TX-12"),
            ("amount", 0),
            ("category", ""),
            ("type", "spending"),
            ("source", "RR-xx:2024-01"),
        ):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self._tx(**{field: bad})

    def test_seq_and_month(self) -> None:
        tx = self._tx()
        self.assertEqual(tx.seq, 12)
        self.assertEqual(tx.month, "2024-01")

    def test_roundtrip(self) -> None:
        tx = self._tx()
        self.assertEqual(Transaction.from_dict(tx.to_dict()), tx)

    def test_source_omitted_when_absent(self) -> None:
        self.assertNotIn("source", self._tx().to_dict())

    def test_source_roundtrip(self) -> None:
        tx = self._tx(source="RR-3f9a2c17:2024-01")
        self.assertEqual(Transaction.from_dict(tx.to_dict()).source, "RR-3f9a2c17:2024-01")

    def test_missing_field_reports_name(self) -> None:
        row = self._tx().to_dict()
        del row["category"]
        with self.assertRaises(ValidationError) as ctx:
            Transaction.from_dict(row)
        self.assertIn("category", ctx.exception.message)


class BudgetAndRuleTest(unittest.TestCase):
    def test_budget_validates(self) -> None:
        self.assertEqual(Budget("2024-01", 500000).to_dict()["amount"], 500000)
        with self.assertRaises(ValidationError):
            Budget("2024-13", 1000)
        with self.assertRaises(ValidationError):
            Budget("2024-01", 0)

    def test_rule_source_key(self) -> None:
        rule = RecurringRule(
            id="RR-3f9a2c17", name="월세", day=25, type="expense",
            category="rent", amount=500000,
        )
        self.assertEqual(rule.source_for("2024-01"), "RR-3f9a2c17:2024-01")

    def test_rule_day_bounds(self) -> None:
        for bad in (0, 32):
            with self.subTest(day=bad), self.assertRaises(ValidationError):
                RecurringRule(
                    id="RR-3f9a2c17", name="월세", day=bad, type="expense",
                    category="rent", amount=1000,
                )


class MonthlySummaryTest(unittest.TestCase):
    def _summary(self, budget: int | None = None) -> MonthlySummary:
        return MonthlySummary(
            month="2024-01",
            total_income=3_000_000,
            total_expense=215_000,
            expense_by_category={"rent": 150_000, "food": 45_000, "transport": 20_000},
            budget=budget,
        )

    def test_balance(self) -> None:
        self.assertEqual(self._summary().balance, 2_785_000)

    def test_no_budget_is_normal(self) -> None:
        summary = self._summary()
        self.assertIsNone(summary.usage_rate)
        self.assertFalse(summary.is_over_budget)

    def test_usage_rate_and_over(self) -> None:
        self.assertAlmostEqual(self._summary(500_000).usage_rate, 43.0)
        self.assertFalse(self._summary(215_000).is_over_budget)  # 정확히 100% 는 초과 아님
        self.assertTrue(self._summary(214_999).is_over_budget)

    def test_top_expenses_order_and_tiebreak(self) -> None:
        summary = MonthlySummary(
            month="2024-01", total_income=0, total_expense=200,
            expense_by_category={"b": 100, "a": 100, "c": 50},
        )
        self.assertEqual(summary.top_expenses(2), [("a", 100), ("b", 100)])

    def test_top_must_be_positive(self) -> None:
        with self.assertRaises(ValidationError):
            self._summary().top_expenses(0)

    def test_is_empty(self) -> None:
        empty = MonthlySummary("2024-01", 0, 0, {})
        self.assertTrue(empty.is_empty)


class QueryTest(unittest.TestCase):
    def _tx(self, **over: object) -> Transaction:
        base = dict(
            id="TX-000001", type="expense", date=date(2024, 1, 15),
            amount=1000, category="food", memo="Lunch with team", tags=["Meal"],
        )
        base.update(over)
        return Transaction(**base)  # type: ignore[arg-type]

    def test_empty_query_matches_all(self) -> None:
        self.assertTrue(Query().matches(self._tx()))

    def test_range_is_inclusive_on_both_ends(self) -> None:
        tx = self._tx()
        self.assertTrue(Query(date_from=tx.date, date_to=tx.date).matches(tx))
        self.assertFalse(Query(date_from=date(2024, 1, 16)).matches(tx))
        self.assertFalse(Query(date_to=date(2024, 1, 14)).matches(tx))

    def test_reversed_range_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Query(date_from=date(2024, 2, 1), date_to=date(2024, 1, 1))

    def test_keyword_is_case_insensitive_and_partial(self) -> None:
        self.assertTrue(Query(keyword="lunch").matches(self._tx()))
        self.assertFalse(Query(keyword="dinner").matches(self._tx()))

    def test_tag_is_case_insensitive_exact(self) -> None:
        self.assertTrue(Query(tag="meal").matches(self._tx()))
        self.assertFalse(Query(tag="mea").matches(self._tx()))

    def test_category_is_case_sensitive(self) -> None:
        self.assertFalse(Query(category="Food").matches(self._tx()))
        self.assertTrue(Query(category="food").matches(self._tx()))

    def test_type_filter(self) -> None:
        self.assertFalse(Query(type="income").matches(self._tx()))

    def test_for_month(self) -> None:
        q = Query.for_month("2024-01", category="food")
        self.assertEqual((q.date_from, q.date_to), (date(2024, 1, 1), date(2024, 1, 31)))
        self.assertTrue(q.matches(self._tx()))


if __name__ == "__main__":
    unittest.main()
