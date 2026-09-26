"""카테고리 관리.

목록 조회와 존재 확인은 거래를 쓸 때마다 필요해 `Ledger` 가 갖고 있고,
여기서는 추가·삭제처럼 카테고리 자체를 바꾸는 일을 맡는다. 삭제는 거래를
함께 손대야 해서 `Ledger` 를 통해 처리한다.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from budget_app.errors import NotFoundError, ValidationError
from budget_app.models import Transaction
from budget_app.service.ledger import Ledger
from budget_app.validators import normalize_category


class Categories:
    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger
        self.data = ledger.data

    def list(self) -> list[str]:
        return self.ledger.categories()

    def add(self, name: str) -> str:
        category = normalize_category(name)
        if category in self.ledger.categories():
            raise ValidationError(
                f"이미 등록된 카테고리입니다: {category}", "category list 로 확인하세요."
            )
        self.data.categories.append({"name": category})
        return category

    def count_using(self, name: str) -> int:
        return sum(1 for tx in self.ledger.stream_transactions() if tx.category == name)

    def remove(self, name: str, replace_with: str | None = None) -> int:
        """카테고리를 지운다. 사용 중이면 대체 카테고리로 옮긴 뒤 지운다.

        거래를 먼저 커밋하고 카테고리를 나중에 지운다. 두 파일을 한 번에 바꿀
        수는 없으므로, 중간에 실패해도 참조가 깨지지 않는 방향을 택한다.
        중간 실패 시 쓰이지 않는 카테고리가 남을 뿐이다.
        """
        category = normalize_category(name)
        # 카테고리 파일 검사를 먼저 끝낸다. 거래를 옮긴 뒤에 이 파일이 손상된 걸
        # 알게 되면, 명령은 실패했는데 거래만 바뀐 상태로 남는다.
        registered = self.ledger.categories()
        if category not in registered:
            raise NotFoundError(
                f"등록되지 않은 카테고리입니다: {category}", "category list 로 확인하세요."
            )
        self._reject_if_used_by_rules(category)

        if replace_with is None:
            self._reject_if_used_by_transactions(category)
            moved = 0
        else:
            target = self._resolve_replacement(category, replace_with, registered)
            moved = self._move_transactions(category, target)

        self.data.categories.write_all(
            {"name": item} for item in registered if item != category
        )
        return moved

    def _reject_if_used_by_rules(self, category: str) -> None:
        using = self._rules_using(category)
        if using:
            raise ValidationError(
                f"'{category}' 를 사용하는 반복 규칙이 {using}개 있습니다.",
                "recurring remove 로 규칙을 먼저 정리하세요.",
            )

    def _reject_if_used_by_transactions(self, category: str) -> None:
        used = self.count_using(category)
        if used:
            raise ValidationError(
                f"'{category}' 를 사용하는 거래가 {used}건 있습니다.",
                "--replace-with <카테고리> 로 대체할 카테고리를 지정하세요.",
            )

    @staticmethod
    def _resolve_replacement(
        category: str, replace_with: str, registered: list[str]
    ) -> str:
        target = normalize_category(replace_with)
        if target not in registered:
            raise NotFoundError(
                f"등록되지 않은 카테고리입니다: {target}",
                "category list 로 목록을 보거나 category add 로 등록하세요.",
            )
        if target == category:
            raise ValidationError(
                "대체 카테고리가 삭제할 카테고리와 같습니다.", "다른 카테고리를 지정하세요."
            )
        return target

    def _move_transactions(self, category: str, target: str) -> int:
        """옮긴 건수는 치환하면서 센다. 세려고 파일을 한 번 더 읽지 않는다."""
        moved = 0

        def transform(tx: Transaction) -> dict[str, Any]:
            nonlocal moved
            if tx.category != category:
                return tx.to_dict()
            moved += 1
            return replace(tx, category=target).to_dict()

        self.ledger.rewrite(transform)
        return moved

    def _rules_using(self, category: str) -> int:
        """반복 규칙이 참조하는지 센다.

        규칙 모델을 몰라도 되는 일이라 dict 그대로 읽는다. 여기서 막지 않으면
        규칙만 존재하지 않는 카테고리를 가리킨 채 남는다.
        """
        return sum(
            1
            for row in self.data.recurring.stream()
            if row.get("category") == category
        )


