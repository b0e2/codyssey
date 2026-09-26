"""실제 프로세스로 명령을 실행해 종료 코드와 출력을 확인한다.

단위 테스트는 핸들러가 돌려주는 값만 본다. 사용자가 실제로 받는 것은
프로세스 종료 코드와 stdout/stderr 이므로 그쪽도 직접 확인한다.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class CommandTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.data = self.root / "data"
        self.addCleanup(self._tmp.cleanup)

    def run_cmd(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "budget_app", "--data-dir", str(self.data), *args],
            cwd=REPO,
            input=stdin,
            capture_output=True,
            text=True,
        )

    def add(self, date: str, type: str, category: str, amount: str) -> None:
        result = self.run_cmd("add", stdin=f"{date}\n{type}\n{category}\n{amount}\n\n\n")
        self.assertEqual(result.returncode, 0, result.stderr)


class HelpTest(CommandTestCase):
    COMMANDS = (
        "add list search summary budget category "
        "update delete export import backup repair recurring"
    ).split()

    def test_every_command_has_help(self) -> None:
        for command in self.COMMANDS:
            with self.subTest(command=command):
                result = self.run_cmd(command, "--help")
                self.assertEqual(result.returncode, 0)
                self.assertIn("usage:", result.stdout)

    def test_no_command_prints_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "budget_app"], cwd=REPO, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stdout)


class EveryCommandRunsTest(CommandTestCase):
    """모든 명령을 실제로 한 번씩 실행한다.

    `--help` 만 확인하면 파서에 등록됐는지만 알 수 있다. 핸들러가 없는 메서드를
    부르고 있어도 통과한다. 실제로 `category add` 가 옮겨간 메서드를 부르고 있었고
    이 테스트가 없어 224개가 모두 통과한 채로 남아 있었다.
    """

    def test_no_command_raises_an_unexpected_error(self) -> None:
        out = self.root / "out.csv"
        rule_id = self._register_rule()

        steps: list[tuple[list[str], str]] = [
            (["add"], "2024-01-15\nexpense\nfood\n15000\n점심\nmeal\n"),
            (["list"], ""),
            (["search", "--q", "점심"], ""),
            (["summary", "--month", "2024-01"], ""),
            (["budget", "set", "--month", "2024-01", "--amount", "500000"], ""),
            (["budget", "list"], ""),
            (["category", "add"], "hobby\n"),
            (["category", "list"], ""),
            (["category", "remove", "--name", "hobby"], ""),
            (["update", "--id", "TX-000001", "--amount", "20000"], ""),
            (["export", "--out", str(out), "--month", "2024-01"], ""),
            (["import", "--from", str(out)], ""),
            (["backup"], ""),
            (["repair"], ""),
            (["recurring", "list"], ""),
            (["recurring", "apply", "--month", "2024-02"], ""),
            (["recurring", "remove", "--id", rule_id], ""),
            (["delete", "--id", "TX-000001"], ""),
        ]

        for args, stdin in steps:
            with self.subTest(command=" ".join(args)):
                result = self.run_cmd(*args, stdin=stdin)
                self.assertNotIn("예상치 못한 오류", result.stderr)
                self.assertEqual(result.returncode, 0, result.stderr)

    def _register_rule(self) -> str:
        result = self.run_cmd(
            "recurring", "add", stdin="월세\n25\nexpense\nrent\n500000\n\n\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.split("id=")[1].split()[0]


class HappyPathTest(CommandTestCase):
    def test_add_list_summary(self) -> None:
        self.add("2024-01-15", "expense", "food", "15000")
        self.add("2024-01-14", "income", "salary", "3000000")

        listed = self.run_cmd("list")
        self.assertEqual(listed.returncode, 0)
        self.assertIn("TX-000001", listed.stdout)

        self.run_cmd("budget", "set", "--month", "2024-01", "--amount", "500000")
        summary = self.run_cmd("summary", "--month", "2024-01", "--top", "3")
        self.assertEqual(summary.returncode, 0)
        self.assertIn("총 지출: 15,000원", summary.stdout)
        self.assertIn("사용률 3.0%", summary.stdout)

    def test_data_survives_between_runs(self) -> None:
        self.add("2024-01-15", "expense", "food", "15000")
        self.assertIn("TX-000001", self.run_cmd("list").stdout)
        self.assertIn("food", self.run_cmd("category", "list").stdout)

    def test_export_then_import_round_trip(self) -> None:
        self.add("2024-01-15", "expense", "food", "15000")
        out = self.root / "out.csv"
        exported = self.run_cmd("export", "--out", str(out), "--month", "2024-01")
        self.assertEqual(exported.returncode, 0)
        self.assertIn("(1 records)", exported.stdout)

        imported = self.run_cmd("import", "--from", str(out))
        self.assertEqual(imported.returncode, 0)
        self.assertIn("imported=1", imported.stdout)


class ExitCodeTest(CommandTestCase):
    def test_missing_id_is_three(self) -> None:
        self.run_cmd("list")
        result = self.run_cmd("delete", "--id", "TX-000999")
        self.assertEqual(result.returncode, 3)
        self.assertIn("[오류]", result.stderr)
        self.assertIn("[힌트]", result.stderr)

    def test_bad_input_is_two(self) -> None:
        self.assertEqual(self.run_cmd("summary", "--month", "2024-13").returncode, 2)
        self.assertEqual(self.run_cmd("list", "--limit", "0").returncode, 2)

    def test_one_sided_range_is_two(self) -> None:
        result = self.run_cmd(
            "export", "--out", str(self.root / "o.csv"), "--from", "2024-01-01"
        )
        self.assertEqual(result.returncode, 2)

    def test_top_is_validated_even_without_data(self) -> None:
        # 같은 입력이 데이터 유무에 따라 다르게 판정되면 안 된다.
        self.run_cmd("list")
        self.assertEqual(self.run_cmd("summary", "--month", "2024-01", "--top", "0").returncode, 2)

    def test_export_onto_a_store_file_is_two(self) -> None:
        self.add("2024-01-15", "expense", "food", "15000")
        before = (self.data / "transactions.jsonl").read_bytes()
        result = self.run_cmd(
            "export", "--out", str(self.data / "transactions.jsonl"), "--month", "2024-01"
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.data / "transactions.jsonl").read_bytes(), before)

    def test_corrupt_store_on_write_is_four(self) -> None:
        self.add("2024-01-15", "expense", "food", "15000")
        with (self.data / "transactions.jsonl").open("a", encoding="utf-8") as fp:
            fp.write("broken\n")
        result = self.run_cmd("delete", "--id", "TX-000001")
        self.assertEqual(result.returncode, 4)

    def test_unreadable_data_dir_is_four(self) -> None:
        blocker = self.root / "blocker"
        blocker.write_text("", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "budget_app", "--data-dir", str(blocker), "list"],
            cwd=REPO, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 4)

    def test_no_traceback_reaches_the_user(self) -> None:
        result = self.run_cmd("summary", "--month", "nope")
        self.assertNotIn("Traceback", result.stderr + result.stdout)


class CorruptionTest(CommandTestCase):
    def test_commands_stop_and_point_at_the_line(self) -> None:
        self.add("2024-01-15", "expense", "food", "15000")
        with (self.data / "transactions.jsonl").open("a", encoding="utf-8") as fp:
            fp.write("broken\n")

        result = self.run_cmd("list")
        self.assertEqual(result.returncode, 4)
        self.assertIn("2번째 줄", result.stderr)
        self.assertIn("repair", result.stderr)

    def test_repair_restores_the_file(self) -> None:
        self.add("2024-01-15", "expense", "food", "15000")
        with (self.data / "transactions.jsonl").open("a", encoding="utf-8") as fp:
            fp.write("broken\n")

        repaired = self.run_cmd("repair")
        self.assertEqual(repaired.returncode, 0)
        self.assertIn("1행 격리", repaired.stdout)

        listed = self.run_cmd("list")
        self.assertEqual(listed.returncode, 0)
        self.assertIn("TX-000001", listed.stdout)

    def test_repair_with_nothing_to_do(self) -> None:
        self.run_cmd("list")
        result = self.run_cmd("repair")
        self.assertEqual(result.returncode, 0)
        self.assertIn("정리할 행이 없습니다", result.stdout)


class InteractiveTest(CommandTestCase):
    def test_retries_a_bad_field_then_succeeds(self) -> None:
        result = self.run_cmd(
            "add", stdin="2024-13-40\n2024-01-15\nexpense\nfood\n15000\n\n\n"
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("[저장 완료]", result.stdout)
        self.assertIn("날짜 형식이 올바르지 않습니다", result.stderr)

    def test_three_failures_stop_with_exit_two(self) -> None:
        result = self.run_cmd("add", stdin="a\nb\nc\n")
        self.assertEqual(result.returncode, 2)

    def test_eof_is_reported_without_a_traceback(self) -> None:
        result = self.run_cmd("add", stdin="")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)


class RecurringE2ETest(CommandTestCase):
    def test_apply_is_idempotent(self) -> None:
        added = self.run_cmd("recurring", "add", stdin="월세\n31\nexpense\nrent\n500000\n\n\n")
        self.assertEqual(added.returncode, 0, added.stderr)

        first = self.run_cmd("recurring", "apply", "--month", "2024-02")
        self.assertIn("1건 생성", first.stdout)
        self.assertIn("2024-02-29", first.stdout)  # 말일 보정

        second = self.run_cmd("recurring", "apply", "--month", "2024-02")
        self.assertEqual(second.returncode, 0)
        self.assertIn("없습니다", second.stdout)


if __name__ == "__main__":
    unittest.main()


class RecurringSkipTest(CommandTestCase):
    def test_skipped_rule_is_reported(self) -> None:
        # 카테고리가 사라져 건너뛴 규칙을 알리지 않으면
        # "생성할 내역이 없다"와 구분되지 않는다.
        #
        # `category remove` 는 규칙이 쓰는 카테고리를 막으므로, 이 상태는 파일을
        # 직접 고쳤을 때만 생긴다. 그래도 조용히 넘어가서는 안 된다.
        added = self.run_cmd(
            "recurring", "add", stdin="월세\n25\nexpense\nrent\n500000\n\n\n"
        )
        self.assertEqual(added.returncode, 0, added.stderr)

        categories = self.data / "categories.jsonl"
        kept = [
            line
            for line in categories.read_text(encoding="utf-8").splitlines()
            if '"rent"' not in line
        ]
        categories.write_text("\n".join(kept) + "\n", encoding="utf-8")

        result = self.run_cmd("recurring", "apply", "--month", "2024-03")
        self.assertEqual(result.returncode, 0)
        self.assertIn("월세", result.stderr)
        self.assertIn("건너뜁니다", result.stderr)
