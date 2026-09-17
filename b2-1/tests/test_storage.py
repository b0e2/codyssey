"""JSONL 저장소 테스트."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from budget_app.errors import StorageError
from budget_app.storage import DEFAULT_CATEGORIES, DataDir, JsonlStore


class StoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def store(self, name: str = "rows.jsonl") -> JsonlStore:
        return JsonlStore(self.root / name)

    def write_raw(self, store: JsonlStore, text: str) -> None:
        store.path.write_text(text, encoding="utf-8")


class StreamTest(StoreTestCase):
    def test_missing_file_is_empty(self) -> None:
        self.assertEqual(list(self.store().stream()), [])

    def test_blank_lines_are_not_corruption(self) -> None:
        store = self.store()
        self.write_raw(store, '{"id": 1}\n\n{"id": 2}\n')
        self.assertEqual([r["id"] for r in store.stream()], [1, 2])

    def test_stops_at_the_first_unreadable_row(self) -> None:
        store = self.store()
        self.write_raw(store, '{"id": 1}\nbroken\n{"id": 2}\n')
        with self.assertRaises(StorageError) as ctx:
            list(store.stream())
        self.assertIn("2번째 줄", ctx.exception.message)

    def test_json_that_is_not_an_object_is_unreadable(self) -> None:
        store = self.store()
        self.write_raw(store, "[1, 2]\n")
        with self.assertRaises(StorageError):
            list(store.stream())

    def test_iter_lines_gives_raw_text_for_repair(self) -> None:
        store = self.store()
        self.write_raw(store, '{"id": 1}\nbroken\n')
        self.assertEqual(list(store.iter_lines()), [(1, '{"id": 1}'), (2, "broken")])


class LastRowTest(StoreTestCase):
    def test_empty_and_missing(self) -> None:
        self.assertIsNone(self.store().last_row())
        store = self.store()
        self.write_raw(store, "")
        self.assertIsNone(store.last_row())

    def test_returns_last_row(self) -> None:
        store = self.store()
        self.write_raw(store, '{"id": "TX-000001"}\n{"id": "TX-000002"}\n')
        self.assertEqual(store.last_row(), {"id": "TX-000002"})

    def test_reads_across_block_boundary(self) -> None:
        # 끝에서부터 블록 단위로 읽으므로 4096 바이트를 넘는 파일로 확인한다.
        store = self.store()
        rows = [json.dumps({"id": f"TX-{i:06d}", "pad": "x" * 200}) for i in range(1, 60)]
        self.write_raw(store, "\n".join(rows) + "\n")
        self.assertGreater(store.path.stat().st_size, 4096)
        self.assertEqual(store.last_row()["id"], "TX-000059")

    def test_corrupt_last_row_blocks_numbering(self) -> None:
        store = self.store()
        self.write_raw(store, '{"id": "TX-000001"}\nbroken\n')
        with self.assertRaises(StorageError):
            store.last_row()


class AppendTest(StoreTestCase):
    def test_append_creates_file(self) -> None:
        store = self.store()
        store.append({"id": 1})
        self.assertEqual(list(store.stream()), [{"id": 1}])

    def test_append_refuses_incomplete_last_line(self) -> None:
        # 개행 없이 끝난 파일에 이어쓰면 두 행이 한 줄로 붙어 함께 깨진다.
        store = self.store()
        self.write_raw(store, '{"id": 1}')
        with self.assertRaises(StorageError):
            store.append({"id": 2})
        self.assertEqual(store.path.read_text(encoding="utf-8"), '{"id": 1}')

    def test_append_does_not_reread_existing_rows(self) -> None:
        # 기존 내용을 다시 쓰지 않으므로 읽을 수 없는 행이 있어도 덧붙일 수 있다.
        store = self.store()
        self.write_raw(store, "broken\n")
        store.append({"id": 2})
        self.assertEqual(list(store.iter_lines()), [(1, "broken"), (2, '{"id": 2}')])


class AtomicWriteTest(StoreTestCase):
    def test_write_all_replaces_content(self) -> None:
        store = self.store()
        store.write_all([{"id": 1}, {"id": 2}])
        self.assertEqual([r["id"] for r in store.stream()], [1, 2])

    def test_failure_midway_keeps_original(self) -> None:
        store = self.store()
        store.write_all([{"id": 1}, {"id": 2}])

        def exploding():
            yield {"id": 9}
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            store.write_all(exploding())
        self.assertEqual([r["id"] for r in store.stream()], [1, 2])

    def test_failure_leaves_no_temp_file(self) -> None:
        store = self.store()
        store.write_all([{"id": 1}])

        def exploding():
            raise RuntimeError("boom")
            yield  # pragma: no cover

        with self.assertRaises(RuntimeError):
            store.write_all(exploding())
        leftovers = [p.name for p in self.root.iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_rewrite_transforms_and_drops(self) -> None:
        store = self.store()
        store.write_all([{"id": 1}, {"id": 2}, {"id": 3}])
        written = store.rewrite(lambda row: None if row["id"] == 2 else {**row, "seen": True})
        self.assertEqual(written, 2)
        self.assertEqual([r["id"] for r in store.stream()], [1, 3])

    def test_rewrite_aborts_on_corruption_and_preserves_file(self) -> None:
        store = self.store()
        self.write_raw(store, '{"id": 1}\nbroken\n{"id": 3}\n')
        before = store.path.read_text(encoding="utf-8")
        with self.assertRaises(StorageError):
            store.rewrite(lambda row: row)
        self.assertEqual(store.path.read_text(encoding="utf-8"), before)


class DataDirTest(StoreTestCase):
    def test_ensure_creates_files_and_seeds_categories(self) -> None:
        data = DataDir(self.root / "data")
        self.assertTrue(data.ensure())
        names = [row["name"] for row in data.categories.stream()]
        self.assertEqual(names, list(DEFAULT_CATEGORIES))
        for store in data.stores:
            self.assertTrue(store.path.exists())

    def test_ensure_is_idempotent(self) -> None:
        data = DataDir(self.root / "data")
        data.ensure()
        self.assertFalse(data.ensure())

    def test_backup_copies_data_files_only(self) -> None:
        data = DataDir(self.root / "data")
        data.ensure()
        (data.root / "app.log").write_text("noise\n", encoding="utf-8")
        dest = data.backup()
        copied = sorted(p.name for p in dest.iterdir())
        self.assertEqual(
            copied,
            ["budgets.jsonl", "categories.jsonl", "recurring.jsonl", "transactions.jsonl"],
        )

    def test_backup_avoids_name_collision(self) -> None:
        data = DataDir(self.root / "data")
        data.ensure()
        first = data.backup("20240115-103000")
        second = data.backup("20240115-103000")
        self.assertNotEqual(first, second)
        self.assertTrue(second.name.endswith("-2"))


if __name__ == "__main__":
    unittest.main()
