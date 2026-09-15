"""CSV 가져오기·내보내기 테스트."""

from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from budget_app.models import Query, StorageError, ValidationError
from budget_app.service.ledger import Ledger
from budget_app.service.porting import CSV_COLUMNS, Porting
from budget_app.storage import DataDir


class PortingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.data = DataDir(self.root / "data")
        self.data.ensure()
        self.addCleanup(self._tmp.cleanup)

    def porting(self) -> Porting:
        return Porting(Ledger(self.data))

    def add(self, day: str, amount: int = 1000, **over) -> None:
        params = dict(
            date=date.fromisoformat(day), type="expense", category="food", amount=amount
        )
        params.update(over)
        Ledger(self.data).create(**params)

    def write_csv(self, name: str, lines: list[str]) -> Path:
        path = self.root / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))


class ExportTest(PortingTestCase):
    def test_header_and_count(self) -> None:
        self.add("2024-01-15")
        out = self.root / "out.csv"
        count = self.porting().export(Query.for_month("2024-01"), out)
        self.assertEqual(count, 1)
        with out.open(encoding="utf-8") as fp:
            self.assertEqual(fp.readline().strip(), ",".join(CSV_COLUMNS))

    def test_ascending_by_date(self) -> None:
        # 다시 가져올 때 저장 순서와 날짜 순서가 같아지도록 오름차순으로 쓴다.
        self.add("2024-01-20")
        self.add("2024-01-05")
        out = self.root / "out.csv"
        self.porting().export(Query.for_month("2024-01"), out)
        self.assertEqual(
            [r["date"] for r in self.read_csv(out)], ["2024-01-05", "2024-01-20"]
        )

    def test_period_filter(self) -> None:
        self.add("2024-01-15")
        self.add("2024-02-15")
        out = self.root / "out.csv"
        self.assertEqual(self.porting().export(Query.for_month("2024-02"), out), 1)

    def test_comma_inside_memo_and_tags_round_trips(self) -> None:
        # 태그 구분자가 쉼표라 CSV 필드 구분자와 겹친다. 표준 인용으로 해결된다.
        self.add("2024-01-15", memo="점심, 회식", tags=["meal", "work"])
        out = self.root / "out.csv"
        self.porting().export(Query.for_month("2024-01"), out)
        row = self.read_csv(out)[0]
        self.assertEqual(row["memo"], "점심, 회식")
        self.assertEqual(row["tags"], "meal,work")

    def test_empty_result_still_writes_header(self) -> None:
        out = self.root / "out.csv"
        self.assertEqual(self.porting().export(Query.for_month("2024-09"), out), 0)
        self.assertEqual(self.read_csv(out), [])


class ImportTest(PortingTestCase):
    def test_partial_success_reports_each_failure(self) -> None:
        src = self.write_csv(
            "in.csv",
            [
                "date,type,category,amount,memo,tags",
                "2024-02-01,expense,food,12000,아침,meal",
                "2024-13-01,expense,food,1000,잘못된 날짜,",
                "2024-02-03,expense,unknown,1000,미등록,",
                "2024-02-04,expense,food,-5,음수,",
            ],
        )
        result = self.porting().import_csv(src)
        self.assertEqual((result.imported, result.skipped), (1, 3))
        self.assertEqual([line for line, _ in result.failures], [3, 4, 5])

        rows = self.read_csv(result.errors_path)
        self.assertEqual([r["line_no"] for r in rows], ["3", "4", "5"])
        self.assertIn("카테고리", rows[1]["reason"])

    def test_no_errors_file_when_everything_is_valid(self) -> None:
        src = self.write_csv(
            "in.csv",
            ["date,type,category,amount,memo,tags", "2024-02-01,expense,food,1200,,"],
        )
        result = self.porting().import_csv(src)
        self.assertIsNone(result.errors_path)
        self.assertEqual(result.imported, 1)

    def test_ids_continue_from_existing_rows(self) -> None:
        self.add("2024-01-01")
        src = self.write_csv(
            "in.csv",
            [
                "date,type,category,amount,memo,tags",
                "2024-02-01,expense,food,1,,",
                "2024-02-02,expense,food,2,,",
            ],
        )
        self.porting().import_csv(src)
        ids = [row["id"] for row in self.data.transactions.stream()]
        self.assertEqual(ids, ["TX-000001", "TX-000002", "TX-000003"])

    def test_existing_rows_survive(self) -> None:
        self.add("2024-01-01", 999)
        src = self.write_csv(
            "in.csv", ["date,type,category,amount,memo,tags", "2024-02-01,expense,food,1,,"]
        )
        self.porting().import_csv(src)
        self.assertEqual(len(list(self.data.transactions.stream())), 2)

    def test_optional_columns_may_be_absent(self) -> None:
        src = self.write_csv("in.csv", ["date,type,category,amount", "2024-02-01,expense,food,1"])
        self.assertEqual(self.porting().import_csv(src).imported, 1)

    def test_missing_required_column(self) -> None:
        src = self.write_csv("in.csv", ["date,type,amount", "2024-02-01,expense,1"])
        with self.assertRaises(ValidationError) as ctx:
            self.porting().import_csv(src)
        self.assertIn("category", ctx.exception.message)

    def test_missing_file(self) -> None:
        with self.assertRaises(StorageError):
            self.porting().import_csv(self.root / "nope.csv")

    def test_corrupt_store_aborts_without_partial_write(self) -> None:
        self.add("2024-01-01")
        with self.data.transactions.path.open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
        before = self.data.transactions.path.read_text(encoding="utf-8")
        src = self.write_csv(
            "in.csv", ["date,type,category,amount,memo,tags", "2024-02-01,expense,food,1,,"]
        )
        with self.assertRaises(StorageError):
            self.porting().import_csv(src)
        self.assertEqual(self.data.transactions.path.read_text(encoding="utf-8"), before)

    def test_all_rows_invalid_changes_nothing(self) -> None:
        self.add("2024-01-01")
        src = self.write_csv(
            "in.csv", ["date,type,category,amount,memo,tags", "bad,expense,food,1,,"]
        )
        result = self.porting().import_csv(src)
        self.assertEqual((result.imported, result.skipped), (0, 1))
        self.assertEqual(len(list(self.data.transactions.stream())), 1)


class RoundTripTest(PortingTestCase):
    def test_reimport_duplicates_by_design(self) -> None:
        # CSV 에는 id 가 없다. 같은 파일을 다시 넣으면 새 거래로 쌓인다.
        self.add("2024-01-15", 1000)
        out = self.root / "out.csv"
        self.porting().export(Query.for_month("2024-01"), out)
        self.porting().import_csv(out)
        self.assertEqual(len(list(self.data.transactions.stream())), 2)


if __name__ == "__main__":
    unittest.main()
