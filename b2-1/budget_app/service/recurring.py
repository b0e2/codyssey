"""반복 내역.

월세·월급처럼 매달 같은 거래를 규칙으로 등록해 두고 특정 월에 생성한다.
핵심은 멱등성이다. 같은 달에 두 번 적용해도 거래가 두 번 생기면 안 된다.
"""

from __future__ import annotations

from budget_app.models import (
    NotFoundError,
    RecurringRule,
    StorageError,
    Transaction,
    ValidationError,
    clamp_day,
    new_rule_id,
    parse_month,
)
from budget_app.service.ledger import Ledger


class Recurring:
    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger
        self.data = ledger.data
        self.warnings: list[str] = []

    # ── 규칙 ────────────────────────────────────────────────────────────

    def rules(self) -> list[RecurringRule]:
        items: list[RecurringRule] = []
        for row in self.data.recurring.stream():
            try:
                items.append(RecurringRule.from_dict(row))
            except ValidationError:
                continue  # 손상된 규칙 행은 목록에서 빼고 조회를 막지 않는다
        return items

    def add(self, rule: RecurringRule) -> RecurringRule:
        self.ledger.require_category(rule.category)
        self.data.recurring.append(rule.to_dict())
        return rule

    def create(
        self,
        *,
        name: str,
        day: int,
        type: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: list[str] | None = None,
    ) -> RecurringRule:
        return self.add(
            RecurringRule(
                id=new_rule_id(),
                name=name,
                day=day,
                type=type,  # type: ignore[arg-type]
                category=category,
                amount=amount,
                memo=memo,
                tags=tags or [],
            )
        )

    def remove(self, rule_id: str) -> RecurringRule:
        target = next((r for r in self.rules() if r.id == rule_id), None)
        if target is None:
            raise NotFoundError(
                f"반복 규칙을 찾을 수 없습니다: {rule_id}",
                "recurring list 로 id 를 확인하세요.",
            )
        self.data.recurring.write_all(
            r.to_dict() for r in self.rules() if r.id != rule_id
        )
        return target

    # ── 적용 ────────────────────────────────────────────────────────────

    def applied_sources(self) -> set[str]:
        """이미 생성된 거래의 출처. 중복이 있으면 유일키가 깨진 것이므로 멈춘다."""
        seen: set[str] = set()
        for tx in self.ledger.stream_transactions():
            if tx.source is None:
                continue
            if tx.source in seen:
                raise StorageError(
                    f"같은 출처의 거래가 두 건 이상 있습니다: {tx.source}",
                    "중복된 거래를 정리한 뒤 다시 실행하세요.",
                )
            seen.add(tx.source)
        return seen

    def apply(self, month: str) -> list[Transaction]:
        """해당 월에 규칙을 적용한다. 이미 적용된 규칙은 건너뛴다.

        생성한 거래에 `<규칙 id>:<월>` 을 출처로 남겨 두는 것이 멱등성의 전부다.
        규칙 id 가 uuid 라서, 규칙을 지우고 새로 만들어도 옛 거래와 겹치지 않는다.
        """
        target = parse_month(month)
        done = self.applied_sources()
        categories = set(self.ledger.categories())
        created: list[Transaction] = []

        for rule in self.rules():
            source = rule.source_for(target)
            if source in done:
                continue
            if rule.category not in categories:
                self.warnings.append(
                    f"[경고] '{rule.name}' 규칙의 카테고리 '{rule.category}' 가 없어 건너뜁니다."
                )
                continue
            created.append(
                self.ledger.create(
                    date=clamp_day(target, rule.day),
                    type=rule.type,
                    category=rule.category,
                    amount=rule.amount,
                    memo=rule.memo,
                    tags=rule.tags,
                    source=source,
                )
            )
        return created
