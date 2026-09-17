"""도메인 데이터 구조와 불변식.

값을 담고 자기 규칙을 지킬 뿐, 어디에 어떻게 저장되는지는 모른다.
파생값은 필드로 두지 않고 속성으로 계산한다. 저장해 두면 집계 결과와 어긋난다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from budget_app.errors import ValidationError
from budget_app.validators import (
    TxType,
    month_range,
    normalize_category,
    parse_amount,
    parse_date,
    parse_month,
    parse_rule_id,
    parse_source,
    parse_tags,
    parse_tx_id,
    parse_type,
)

@dataclass(frozen=True)
class Context:
    """명령 실행에 필요한 환경. 전역 상태 대신 핸들러로 명시적으로 전달한다."""

    data_dir: Path
    verbose: bool = False

    @property
    def log_path(self) -> Path:
        return self.data_dir / "app.log"



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
        if self.source is not None:
            self.source = parse_source(self.source)

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
        self.id = parse_rule_id(self.id)
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
