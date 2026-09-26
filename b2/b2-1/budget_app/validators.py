"""원시 값의 규칙.

날짜·금액·타입·카테고리명처럼 문자열로 들어오는 값을 도메인이 쓰는 형태로
바꾼다. 형식이 틀리면 원인과 예시를 함께 알린다.

CLI 가 입력을 받을 때도, 저장된 행을 모델로 되돌릴 때도 같은 함수를 쓴다.
검증 규칙이 두 벌로 갈라지지 않는다.
"""

from __future__ import annotations

import calendar
import re
import uuid
from datetime import date, datetime
from typing import Iterable, Literal

from budget_app.errors import StorageError, ValidationError

TxType = Literal["income", "expense"]

TX_TYPES: tuple[TxType, ...] = ("income", "expense")

MAX_TX_SEQ = 999_999
MAX_CATEGORY_LEN = 32

_TX_ID_RE = re.compile(r"^TX-\d{6}$")
_RULE_ID_RE = re.compile(r"^RR-[0-9a-f]{8}$")
_SOURCE_RE = re.compile(r"^RR-[0-9a-f]{8}:\d{4}-\d{2}$")
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_FORBIDDEN_IN_CATEGORY = (",", "\n", "\t")



def parse_date(raw: str) -> date:
    """`YYYY-MM-DD` 만 허용한다.

    strptime 은 `2024-1-5` 도 받아들이므로 왕복 비교로 자릿수까지 고정한다.
    """
    text = raw.strip()
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", "예: 2024-01-15"
        ) from None
    if parsed.isoformat() != text:
        raise ValidationError(
            "날짜는 자리를 채워 입력해야 합니다 (YYYY-MM-DD).", "예: 2024-01-05"
        )
    return parsed


def parse_month(raw: str) -> str:
    """`YYYY-MM` 을 검증하고 그대로 돌려준다."""
    text = raw.strip()
    if not _MONTH_RE.match(text):
        raise ValidationError(
            "월 형식이 올바르지 않습니다 (YYYY-MM).", "예: 2024-01"
        )
    return text


def month_range(month: str) -> tuple[date, date]:
    """해당 월의 첫날과 마지막 날. 요약·내보내기가 기간 조건으로 쓴다."""
    text = parse_month(month)
    year, mon = int(text[:4]), int(text[5:])
    last = calendar.monthrange(year, mon)[1]
    return date(year, mon, 1), date(year, mon, last)


def clamp_day(month: str, day: int) -> date:
    """그 달에 없는 날짜는 말일로 보정한다 (1/31 규칙 -> 2월 말일)."""
    if not 1 <= day <= 31:
        raise ValidationError("일자는 1~31 사이여야 합니다.", f"입력값: {day}")
    first, last = month_range(month)
    return first.replace(day=min(day, last.day))


def parse_amount(raw: str | int) -> int:
    """양의 정수만 허용한다. 0과 음수는 거래로 의미가 없다."""
    if isinstance(raw, bool) or not isinstance(raw, (str, int)):
        raise ValidationError("금액은 정수여야 합니다.", "예: 15000")
    text = str(raw).strip()
    if not re.fullmatch(r"[+-]?\d+", text):
        raise ValidationError("금액은 정수여야 합니다.", "예: 15000")
    value = int(text)
    if value <= 0:
        raise ValidationError("금액은 0보다 커야 합니다.", "예: 15000")
    return value


def parse_type(raw: str) -> TxType:
    text = raw.strip()
    if text not in TX_TYPES:
        raise ValidationError(
            "타입은 income 또는 expense 여야 합니다.", f"입력값: {raw!r}"
        )
    return text  # type: ignore[return-value]


def normalize_category(raw: str) -> str:
    """카테고리명 정규화. 대소문자는 구분한다."""
    name = raw.strip()
    if not name:
        raise ValidationError("카테고리명은 비어 있을 수 없습니다.", "예: food")
    if len(name) > MAX_CATEGORY_LEN:
        raise ValidationError(
            f"카테고리명은 {MAX_CATEGORY_LEN}자 이하여야 합니다.", f"입력 길이: {len(name)}"
        )
    for ch in _FORBIDDEN_IN_CATEGORY:
        if ch in name:
            raise ValidationError(
                "카테고리명에 쉼표·탭·줄바꿈을 쓸 수 없습니다.", f"입력값: {raw!r}"
            )
    return name


def parse_tags(raw: str | Iterable[str] | None) -> list[str]:
    """쉼표 구분 문자열 또는 문자열 목록을 태그 목록으로 만든다.

    빈 값은 버리고 중복은 입력 순서를 유지한 채 제거한다.
    """
    if raw is None:
        return []
    items = raw.split(",") if isinstance(raw, str) else list(raw)
    tags: list[str] = []
    for item in items:
        tag = str(item).strip()
        if not tag:
            continue
        if tag not in tags:
            tags.append(tag)
    return tags


def parse_tx_id(raw: str) -> str:
    text = raw.strip()
    if not _TX_ID_RE.match(text):
        raise ValidationError("거래 id 형식이 올바르지 않습니다.", "예: TX-000012")
    return text


def format_tx_id(seq: int) -> str:
    if not 1 <= seq <= MAX_TX_SEQ:
        raise StorageError(
            f"거래 번호가 한계({MAX_TX_SEQ})를 넘었습니다.",
            "데이터를 분리하거나 다른 저장소로 옮겨야 합니다.",
        )
    return f"TX-{seq:06d}"


def new_rule_id() -> str:
    """반복 규칙 id.

    거래 id 와 달리 순번을 쓰지 않는다. 규칙 id 는 거래의 `source` 가 참조하는
    키라서, 삭제 후 재등록으로 번호가 재사용되면 옛 거래와 충돌해 적용이 no-op 이 된다.
    """
    return f"RR-{uuid.uuid4().hex[:8]}"




def parse_rule_id(raw: str) -> str:
    text = raw.strip()
    if not _RULE_ID_RE.match(text):
        raise ValidationError("규칙 id 형식이 올바르지 않습니다.", "예: RR-3f9a2c17")
    return text


def parse_source(raw: str) -> str:
    text = raw.strip()
    if not _SOURCE_RE.match(text):
        raise ValidationError(
            "source 형식이 올바르지 않습니다.", "예: RR-3f9a2c17:2024-01"
        )
    return text
