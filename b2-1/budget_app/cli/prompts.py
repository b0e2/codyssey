"""대화형 입력.

값을 하나씩 물어보고, 형식이 틀리면 그 항목만 다시 묻는다. 한 항목이
틀렸다고 처음부터 다시 입력하게 만들지 않는다.
"""

from __future__ import annotations

from budget_app.cli.render import warn
from budget_app.errors import AppError, ValidationError

MAX_INPUT_ATTEMPTS = 3


def ask(label: str, parse, *, optional: bool = False):
    """값 하나를 받는다. 형식이 틀리면 원인을 보여주고 다시 묻는다."""
    for _ in range(MAX_INPUT_ATTEMPTS):
        try:
            raw = input(f"{label}: ")
        except EOFError:
            raise ValidationError(
                "입력이 중단되었습니다.", "대화형 입력이 필요한 명령입니다."
            ) from None
        if optional and not raw.strip():
            return parse("")
        try:
            return parse(raw)
        except AppError as exc:
            warn(f"[오류] {exc.message}", *( [f"[힌트] {exc.hint}"] if exc.hint else [] ))
    raise ValidationError(
        f"{label} 입력을 {MAX_INPUT_ATTEMPTS}회 확인하지 못해 중단합니다.",
        "값을 확인한 뒤 다시 실행하세요.",
    )


def require_text(label: str):
    """비어 있으면 거부하는 입력 변환기."""

    def parse(raw: str) -> str:
        text = raw.strip()
        if not text:
            raise ValidationError(f"{label}은(는) 비어 있을 수 없습니다.", "값을 입력하세요.")
        return text

    return parse


def parse_day(raw: str) -> int:
    text = raw.strip()
    if not text.isdigit() or not 1 <= int(text) <= 31:
        raise ValidationError("일자는 1~31 사이의 정수여야 합니다.", "예: 25")
    return int(text)
