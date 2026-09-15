"""애플리케이션 단위 테스트."""

from __future__ import annotations

import unittest
from pathlib import Path

from budget_app.cli.app import build_parser


class GlobalOptionPositionTest(unittest.TestCase):
    """전역 옵션은 서브커맨드 앞뒤 어디에 와도 같게 동작해야 한다."""

    def setUp(self) -> None:
        self.parser = build_parser()

    def test_option_before_subcommand_survives(self) -> None:
        # 서브파서 기본값이 앞쪽 값을 덮어쓰지 않는지 확인한다.
        args = self.parser.parse_args(["--data-dir", "/tmp/a", "list"])
        self.assertEqual(args.data_dir, Path("/tmp/a"))

    def test_option_after_subcommand(self) -> None:
        args = self.parser.parse_args(["list", "--data-dir", "/tmp/a"])
        self.assertEqual(args.data_dir, Path("/tmp/a"))

    def test_later_occurrence_wins(self) -> None:
        args = self.parser.parse_args(
            ["--data-dir", "/tmp/a", "list", "--data-dir", "/tmp/b"]
        )
        self.assertEqual(args.data_dir, Path("/tmp/b"))

    def test_default_applies_when_absent(self) -> None:
        args = self.parser.parse_args(["list"])
        self.assertEqual(args.data_dir, Path("./data"))
        self.assertFalse(args.verbose)

    def test_nested_subcommand_keeps_leading_option(self) -> None:
        args = self.parser.parse_args(["--verbose", "budget", "list"])
        self.assertTrue(args.verbose)


class SubcommandRegistrationTest(unittest.TestCase):
    """필수 명령이 모두 파서에 등록되어 있어야 한다."""

    EXPECTED = (
        "add list search summary budget category "
        "update delete export import backup recurring"
    ).split()

    def test_all_commands_registered(self) -> None:
        parser = build_parser()
        for name in self.EXPECTED:
            with self.subTest(command=name):
                args = parser.parse_args(self._minimal_argv(name))
                self.assertEqual(args.command, name)

    @staticmethod
    def _minimal_argv(command: str) -> list[str]:
        required = {
            "summary": ["--month", "2024-01"],
            "update": ["--id", "TX-000001", "--amount", "1000"],
            "delete": ["--id", "TX-000001"],
            "export": ["--out", "out.csv", "--month", "2024-01"],
            "import": ["--from", "in.csv"],
        }
        return [command, *required.get(command, [])]


if __name__ == "__main__":
    unittest.main()
