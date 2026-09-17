"""콘솔 출력 포맷.

외부 라이브러리 없이 열을 맞춘다. 한글은 터미널에서 두 칸을 차지하므로
문자 수가 아니라 표시 폭으로 계산해야 정렬이 어긋나지 않는다.
"""

from __future__ import annotations

import sys
import unicodedata
from typing import Iterable, Literal, Sequence

from budget_app.models import Transaction

Align = Literal["left", "right"]

ELLIPSIS = "…"


def warn(*lines: str) -> None:
    """경고와 안내는 결과와 섞이지 않도록 stderr 로 보낸다."""
    for line in lines:
        print(line, file=sys.stderr)


def display_width(text: str) -> int:
    """터미널에서 차지하는 칸 수. 한중일 전각 문자는 2로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def truncate(text: str, width: int) -> str:
    """표시 폭 기준으로 자른다. 문자 수로 자르면 한글에서 열이 밀린다."""
    if width <= 0:
        return ""
    if display_width(text) <= width:
        return text
    budget = width - display_width(ELLIPSIS)
    out: list[str] = []
    used = 0
    for ch in text:
        step = display_width(ch)
        if used + step > budget:
            break
        out.append(ch)
        used += step
    return "".join(out) + ELLIPSIS


def pad(text: str, width: int, align: Align = "left") -> str:
    text = truncate(text, width)
    space = " " * max(0, width - display_width(text))
    return space + text if align == "right" else text + space


def format_amount(value: int) -> str:
    """천 단위 구분자. 금액 자릿수를 눈으로 비교할 수 있게 한다."""
    return f"{value:,}"


def render_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    aligns: Sequence[Align] | None = None,
    max_widths: Sequence[int] | None = None,
) -> str:
    """헤더·구분선·본문으로 이루어진 표를 문자열로 만든다."""
    if not headers:
        return ""
    aligns = list(aligns or ["left"] * len(headers))
    widths = [display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], display_width(cell))
    if max_widths:
        widths = [min(w, m) if m else w for w, m in zip(widths, max_widths)]

    lines = [" | ".join(pad(h, w, a) for h, w, a in zip(headers, widths, aligns))]
    lines.append("-+-".join("-" * w for w in widths))
    for row in rows:
        lines.append(" | ".join(pad(c, w, a) for c, w, a in zip(row, widths, aligns)))
    return "\n".join(lines)


def render_lines(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


_TABLE_HEADERS = ("id", "날짜", "타입", "카테고리", "금액", "메모", "태그")
_TABLE_ALIGNS = ("left", "left", "left", "left", "right", "left", "left")
_MEMO_MAX_WIDTH = 24


def print_transactions(rows: list[Transaction]) -> None:
    if not rows:
        print("[안내] 조건에 맞는 거래가 없습니다.")
        return
    table = render_table(
        _TABLE_HEADERS,
        [
            [
                tx.id,
                tx.date.isoformat(),
                tx.type,
                tx.category,
                format_amount(tx.amount),
                tx.memo,
                ",".join(tx.tags),
            ]
            for tx in rows
        ],
        _TABLE_ALIGNS,
        max_widths=[0, 0, 0, 0, 0, _MEMO_MAX_WIDTH, 0],
    )
    print(table)
    print(f"\n총 {len(rows)}건")
