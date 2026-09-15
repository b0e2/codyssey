"""도메인 데이터 구조와 불변식.

이 모듈은 패키지 안의 어떤 모듈도 import 하지 않는다. 의존 그래프의 최하단이며,
행동 없이 값만 갖는 구조는 실행 컨텍스트(`Context`)까지 포함해 전부 여기에 둔다.
"""

from __future__ import annotations

import calendar
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Literal

# ── 타입 ──────────────────────────────────────────────────────────────────

TxType = Literal["income", "expense"]

TX_TYPES: tuple[TxType, ...] = ("income", "expense")

MAX_TX_SEQ = 999_999
MAX_CATEGORY_LEN = 32

_TX_ID_RE = re.compile(r"^TX-\d{6}$")
_RULE_ID_RE = re.compile(r"^RR-[0-9a-f]{8}$")
_SOURCE_RE = re.compile(r"^RR-[0-9a-f]{8}:\d{4}-\d{2}$")
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_FORBIDDEN_IN_CATEGORY = (",", "\n", "\t")


# ── 예외 ──────────────────────────────────────────────────────────────────


class AppError(Exception):
    """사용자에게 원인과 해결 힌트를 보여줄 수 있는 오류.

    스택트레이스 대신 message + hint 를 출력하고 exit_code 로 종료하기 위해
    종료 코드를 예외 자신이 들고 다닌다.
    """

    exit_code = 1

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(AppError):
    """입력 형식·값이 규칙에 맞지 않음."""

    exit_code = 2


class NotFoundError(AppError):
    """존재해야 할 자원을 찾지 못함 (거래 id, 카테고리, 규칙)."""

    exit_code = 3


class StorageError(AppError):
    """파일 I/O 실패 또는 저장 데이터 손상."""

    exit_code = 4


# ── 실행 컨텍스트 ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Context:
    """명령 실행에 필요한 환경. 전역 상태 대신 핸들러로 명시적으로 전달한다."""

    data_dir: Path
    verbose: bool = False

    @property
    def log_path(self) -> Path:
        return self.data_dir / "app.log"


# ── 검증 ──────────────────────────────────────────────────────────────────


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


# ── 데이터 모델 ────────────────────────────────────────────────────────────


@dataclass
class Transaction:
    id: str
    type: TxType
    date: date
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)
    source: str | None = None

    def __post_init__(self) -> None:
        self.id = parse_tx_id(self.id)
        self.type = parse_type(self.type)
        if not isinstance(self.date, date):
            raise ValidationError("날짜는 date 값이어야 합니다.", f"입력값: {self.date!r}")
        self.amount = parse_amount(self.amount)
        self.category = normalize_category(self.category)
        self.memo = (self.memo or "").strip()
        self.tags = parse_tags(self.tags)
        if self.source is not None and not _SOURCE_RE.match(self.source):
            raise ValidationError(
                "source 형식이 올바르지 않습니다.", "예: RR-3f9a2c17:2024-01"
            )

    @property
    def seq(self) -> int:
        """정렬 키로 쓰는 일련번호. id 형식이 불변식으로 보장되어 항상 파싱된다."""
        return int(self.id[3:])

    @property
    def month(self) -> str:
        return self.date.strftime("%Y-%m")

    def to_dict(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "date": self.date.isoformat(),
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": list(self.tags),
        }
        if self.source is not None:
            row["source"] = self.source
        return row

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> Transaction:
        try:
            return cls(
                id=str(row["id"]),
                type=str(row["type"]),  # type: ignore[arg-type]
                date=parse_date(str(row["date"])),
                amount=row["amount"],
                category=str(row["category"]),
                memo=str(row.get("memo", "")),
                tags=row.get("tags") or [],
                source=row.get("source"),
            )
        except KeyError as exc:
            raise ValidationError(
                f"거래에 필수 항목이 없습니다: {exc.args[0]}",
                "date, type, category, amount, id 가 모두 있어야 합니다.",
            ) from None


@dataclass
class Budget:
    month: str
    amount: int

    def __post_init__(self) -> None:
        self.month = parse_month(self.month)
        self.amount = parse_amount(self.amount)

    def to_dict(self) -> dict[str, Any]:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> Budget:
        try:
            return cls(month=str(row["month"]), amount=row["amount"])
        except KeyError as exc:
            raise ValidationError(
                f"예산에 필수 항목이 없습니다: {exc.args[0]}", "month, amount 가 필요합니다."
            ) from None


@dataclass
class RecurringRule:
    id: str
    name: str
    day: int
    type: TxType
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not _RULE_ID_RE.match(self.id):
            raise ValidationError(
                "규칙 id 형식이 올바르지 않습니다.", "예: RR-3f9a2c17"
            )
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError("규칙 이름은 비어 있을 수 없습니다.", "예: 월세")
        if not isinstance(self.day, int) or isinstance(self.day, bool):
            raise ValidationError("일자는 정수여야 합니다.", "예: 25")
        if not 1 <= self.day <= 31:
            raise ValidationError("일자는 1~31 사이여야 합니다.", f"입력값: {self.day}")
        self.type = parse_type(self.type)
        self.category = normalize_category(self.category)
        self.amount = parse_amount(self.amount)
        self.memo = (self.memo or "").strip()
        self.tags = parse_tags(self.tags)

    def source_for(self, month: str) -> str:
        """이 규칙이 해당 월에 만든 거래를 식별하는 키."""
        return f"{self.id}:{parse_month(month)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "day": self.day,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "memo": self.memo,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> RecurringRule:
        try:
            return cls(
                id=str(row["id"]),
                name=str(row["name"]),
                day=row["day"],
                type=str(row["type"]),  # type: ignore[arg-type]
                category=str(row["category"]),
                amount=row["amount"],
                memo=str(row.get("memo", "")),
                tags=row.get("tags") or [],
            )
        except KeyError as exc:
            raise ValidationError(
                f"반복 규칙에 필수 항목이 없습니다: {exc.args[0]}",
                "id, name, day, type, category, amount 가 필요합니다.",
            ) from None


@dataclass(frozen=True)
class MonthlySummary:
    """월 요약. 파생값은 필드로 저장하지 않고 속성으로 계산한다."""

    month: str
    total_income: int
    total_expense: int
    expense_by_category: dict[str, int]
    budget: int | None = None

    @property
    def balance(self) -> int:
        return self.total_income - self.total_expense

    @property
    def is_empty(self) -> bool:
        return self.total_income == 0 and self.total_expense == 0

    @property
    def usage_rate(self) -> float | None:
        """예산 사용률(%). 예산 미설정은 정상 상태이므로 None 을 돌려준다."""
        if self.budget is None:
            return None
        return self.total_expense / self.budget * 100

    @property
    def is_over_budget(self) -> bool:
        return self.budget is not None and self.total_expense > self.budget

    def top_expenses(self, limit: int) -> list[tuple[str, int]]:
        """지출 상위 N개. 금액 내림차순, 같으면 카테고리 이름 오름차순."""
        if limit <= 0:
            raise ValidationError("--top 은 1 이상이어야 합니다.", f"입력값: {limit}")
        ranked = sorted(self.expense_by_category.items(), key=lambda kv: (-kv[1], kv[0]))
        return ranked[:limit]


# ── 조회 조건 ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Query:
    """거래 필터. list / search / summary / export 가 이 하나를 공유한다.

    저장소는 조건을 모른 채 dict 만 흘리고, 매칭 규칙은 도메인이 소유한다.
    """

    date_from: date | None = None
    date_to: date | None = None
    category: str | None = None
    type: TxType | None = None
    keyword: str | None = None
    tag: str | None = None

    def __post_init__(self) -> None:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(
                "--from 은 --to 보다 늦을 수 없습니다.",
                f"{self.date_from.isoformat()} > {self.date_to.isoformat()}",
            )

    @classmethod
    def for_month(cls, month: str, **extra: Any) -> Query:
        first, last = month_range(month)
        return cls(date_from=first, date_to=last, **extra)

    def matches(self, tx: Transaction) -> bool:
        if self.date_from is not None and tx.date < self.date_from:
            return False
        if self.date_to is not None and tx.date > self.date_to:
            return False
        if self.type is not None and tx.type != self.type:
            return False
        if self.category is not None and tx.category != self.category:
            return False
        if self.keyword is not None and self.keyword.casefold() not in tx.memo.casefold():
            return False
        if self.tag is not None:
            wanted = self.tag.casefold()
            if not any(tag.casefold() == wanted for tag in tx.tags):
                return False
        return True
