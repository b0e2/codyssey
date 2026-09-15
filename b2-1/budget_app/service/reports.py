"""월별 집계와 예산 판정.

거래를 바꾸지 않는 읽기 전용 파생 계층이다. 합계·잔액·사용률 계산식은
도메인(`MonthlySummary`)이 갖고, 여기서는 거래를 훑어 모으는 일만 한다.
"""

from __future__ import annotations

from budget_app.models import (
    Budget,
    MonthlySummary,
    Query,
    ValidationError,
    parse_amount,
    parse_month,
)
from budget_app.service.ledger import Ledger


class Reports:
    """요약과 예산. 거래 읽기는 `Ledger` 를 그대로 쓴다."""

    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger
        self.data = ledger.data

    # ── 예산 ────────────────────────────────────────────────────────────

    def budgets(self) -> list[Budget]:
        items: dict[str, Budget] = {}
        for row in self.data.budgets.stream():
            try:
                budget = Budget.from_dict(row)
            except ValidationError:
                continue  # 손상된 예산 행은 건너뛴다. 조회를 막을 이유가 없다.
            items[budget.month] = budget
        return [items[month] for month in sorted(items)]

    def budget_for(self, month: str) -> int | None:
        target = parse_month(month)
        for budget in self.budgets():
            if budget.month == target:
                return budget.amount
        return None

    def set_budget(self, month: str, amount: int) -> Budget:
        """월 예산을 저장한다. 같은 달이 이미 있으면 덮어쓴다.

        덧붙이기만 하면 같은 달이 여러 줄로 쌓여 어느 값이 맞는지 알 수 없다.
        """
        budget = Budget(parse_month(month), parse_amount(amount))
        merged = {item.month: item for item in self.budgets()}
        merged[budget.month] = budget
        self.data.budgets.write_all(
            merged[key].to_dict() for key in sorted(merged)
        )
        return budget

    # ── 요약 ────────────────────────────────────────────────────────────

    def summarize(self, month: str) -> MonthlySummary:
        target = parse_month(month)
        query = Query.for_month(target)
        income = 0
        expense = 0
        by_category: dict[str, int] = {}

        for tx in self.ledger.stream_transactions():
            if not query.matches(tx):
                continue
            if tx.type == "income":
                income += tx.amount
            else:
                expense += tx.amount
                by_category[tx.category] = by_category.get(tx.category, 0) + tx.amount

        return MonthlySummary(
            month=target,
            total_income=income,
            total_expense=expense,
            expense_by_category=by_category,
            budget=self.budget_for(target),
        )
