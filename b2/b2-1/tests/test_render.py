"""콘솔 출력 포맷 테스트."""

from __future__ import annotations

import unittest

from budget_app.cli.render import (
    display_width,
    format_amount,
    pad,
    render_table,
    truncate,
)


class WidthTest(unittest.TestCase):
    def test_hangul_counts_two(self) -> None:
        self.assertEqual(display_width("점심"), 4)
        self.assertEqual(display_width("food"), 4)
        self.assertEqual(display_width("점심 약속"), 9)

    def test_pad_uses_display_width(self) -> None:
        # 문자 수로 맞추면 한글 열이 밀린다.
        self.assertEqual(display_width(pad("점심", 10)), 10)
        self.assertEqual(display_width(pad("food", 10)), 10)

    def test_right_align(self) -> None:
        self.assertEqual(pad("15,000", 8, "right"), "  15,000")


class TruncateTest(unittest.TestCase):
    def test_short_text_untouched(self) -> None:
        self.assertEqual(truncate("food", 10), "food")

    def test_cuts_by_width_not_character_count(self) -> None:
        cut = truncate("점심 약속입니다", 8)
        self.assertLessEqual(display_width(cut), 8)
        self.assertTrue(cut.endswith("…"))

    def test_zero_width(self) -> None:
        self.assertEqual(truncate("food", 0), "")


class TableTest(unittest.TestCase):
    def test_columns_line_up_with_mixed_scripts(self) -> None:
        table = render_table(
            ["카테고리", "금액"],
            [["food", "15,000"], ["교통비", "3,000"]],
            ["left", "right"],
        )
        widths = {display_width(line) for line in table.splitlines()}
        self.assertEqual(len(widths), 1)

    def test_has_header_and_separator(self) -> None:
        table = render_table(["a"], [["1"]])
        lines = table.splitlines()
        self.assertEqual(lines[0].strip(), "a")
        self.assertTrue(set(lines[1]) <= {"-", "+"})

    def test_empty_rows_still_renders_header(self) -> None:
        self.assertIn("id", render_table(["id"], []))

    def test_max_width_truncates_column(self) -> None:
        table = render_table(["memo"], [["아주 긴 메모가 들어옵니다"]], max_widths=[10])
        for line in table.splitlines():
            self.assertLessEqual(display_width(line), 10)


class AmountTest(unittest.TestCase):
    def test_thousands_separator(self) -> None:
        self.assertEqual(format_amount(3_000_000), "3,000,000")
        self.assertEqual(format_amount(0), "0")


if __name__ == "__main__":
    unittest.main()
