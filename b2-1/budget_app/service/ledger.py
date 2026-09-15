"""거래 쓰기 경로와 조회.

저장소가 흘리는 dict 를 도메인 객체로 바꾸고, 업무 규칙을 적용한다.
파일 경로는 알지 못한다.
"""

from __future__ import annotations

import heapq
from dataclasses import replace
from typing import Any, Iterator

from budget_app.models import (
    NotFoundError,
    Query,
    StorageError,
    Transaction,
    ValidationError,
    format_tx_id,
    normalize_category,
    parse_tx_id,
)
from budget_app.storage import DataDir, describe_corruption


class Ledger:
    """거래 관련 유스케이스.

    명령 하나당 인스턴스 하나를 만든다. 읽는 동안 건너뛴 손상 행 경고를
    `warnings` 에 모아두면 CLI 가 결과와 함께 보여줄 수 있다.
    """

    def __init__(self, data: DataDir) -> None:
        self.data = data
        self.warnings: list[str] = []

    # ── 카테고리 ────────────────────────────────────────────────────────

    def categories(self) -> list[str]:
        return [
            str(row["name"])
            for row in self.data.categories.stream()
            if isinstance(row.get("name"), str)
        ]

    def require_category(self, name: str) -> str:
        category = normalize_category(name)
        if category not in self.categories():
            raise NotFoundError(
                f"등록되지 않은 카테고리입니다: {category}",
                "category list 로 목록을 보거나 category add 로 등록하세요.",
            )
        return category

    # ── 읽기 ────────────────────────────────────────────────────────────

    def _transactions(self) -> Iterator[Transaction]:
        """정상 행만 흘린다. 손상 행과 규칙에 어긋난 행은 건너뛰고 경고로 모은다."""
        corrupt: list[int] = []
        rows = self.data.transactions.stream(corrupt)
        for line_no, row in enumerate(rows, start=1):
            try:
                yield Transaction.from_dict(row)
            except ValidationError:
                corrupt.append(line_no)
        if corrupt:
            self.warnings.append(
                describe_corruption(self.data.transactions.path, sorted(corrupt))
            )

    def search(self, query: Query, limit: int) -> list[Transaction]:
        """조건에 맞는 거래를 최신순으로 돌려준다.

        정렬이 필요하므로 파일은 끝까지 읽어야 한다. 대신 상위 N개만 들고 있는
        힙을 써서 결과 목록 크기를 limit 으로 묶는다. 파일이 커져도 메모리는
        늘지 않는다.
        """
        if limit <= 0:
            raise ValidationError("--limit 은 1 이상이어야 합니다.", f"입력값: {limit}")
        hits = (tx for tx in self._transactions() if query.matches(tx))
        return heapq.nlargest(limit, hits, key=lambda tx: (tx.date, tx.seq))

    def get(self, tx_id: str) -> Transaction:
        wanted = parse_tx_id(tx_id)
        for tx in self._transactions():
            if tx.id == wanted:
                return tx
        raise NotFoundError(
            f"거래를 찾을 수 없습니다: {wanted}", "list 로 id 를 확인하세요."
        )

    # ── 쓰기 ────────────────────────────────────────────────────────────

    def next_id(self) -> str:
        """마지막 행에서 다음 번호를 얻는다. 파일 전체를 읽지 않는다."""
        row = self.data.transactions.last_row()
        if row is None:
            return format_tx_id(1)
        try:
            last = parse_tx_id(str(row.get("id", "")))
        except ValidationError:
            raise StorageError(
                "마지막 거래의 id 를 읽을 수 없어 번호를 매길 수 없습니다.",
                f"{self.data.transactions.path} 의 마지막 줄을 확인하세요.",
            ) from None
        return format_tx_id(int(last[3:]) + 1)

    def add(self, tx: Transaction) -> Transaction:
        self.require_category(tx.category)
        self.data.transactions.append(tx.to_dict())
        return tx

    def create(
        self,
        *,
        date,
        type,
        category: str,
        amount: int,
        memo: str = "",
        tags: list[str] | None = None,
        source: str | None = None,
    ) -> Transaction:
        return self.add(
            Transaction(
                id=self.next_id(),
                type=type,
                date=date,
                amount=amount,
                category=category,
                memo=memo,
                tags=tags or [],
                source=source,
            )
        )

    # ── 변경 ────────────────────────────────────────────────────────────

    def _rewrite(self, transform) -> None:
        """거래 파일을 통째로 다시 쓴다.

        손상 행이 있으면 저장소가 중단시킨다. 건너뛴 채 다시 쓰면 읽지 못한
        원본이 새 파일에서 사라지기 때문이다.
        """
        self.data.transactions.rewrite(transform)

    def update(self, tx_id: str, changes: dict[str, Any]) -> Transaction:
        if not changes:
            raise ValidationError(
                "변경할 항목이 없습니다.",
                "--date --type --category --amount --memo --tags 중 하나 이상을 지정하세요.",
            )
        wanted = parse_tx_id(tx_id)
        if "category" in changes:
            changes["category"] = self.require_category(changes["category"])

        updated: list[Transaction] = []

        def transform(row: dict[str, Any]) -> dict[str, Any]:
            if row.get("id") != wanted:
                return row
            current = self._to_transaction(row)
            # dataclass replace 가 __post_init__ 을 다시 태우므로 변경분도 검증된다.
            new_tx = replace(current, **changes)
            updated.append(new_tx)
            return new_tx.to_dict()

        self._rewrite(transform)
        if not updated:
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {wanted}", "list 로 id 를 확인하세요."
            )
        return updated[0]

    def delete(self, tx_id: str) -> Transaction:
        wanted = parse_tx_id(tx_id)
        removed: list[Transaction] = []

        def transform(row: dict[str, Any]) -> dict[str, Any] | None:
            if row.get("id") != wanted:
                return row
            removed.append(self._to_transaction(row))
            return None

        self._rewrite(transform)
        if not removed:
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {wanted}", "list 로 id 를 확인하세요."
            )
        return removed[0]

    def _to_transaction(self, row: dict[str, Any]) -> Transaction:
        """쓰기 경로에서는 규칙에 어긋난 행도 손상으로 본다."""
        try:
            return Transaction.from_dict(row)
        except ValidationError as exc:
            raise StorageError(
                f"저장된 거래를 읽을 수 없습니다: {exc.message}",
                f"{self.data.transactions.path} 를 확인하세요.",
            ) from None

    # ── 카테고리 관리 ────────────────────────────────────────────────────

    def add_category(self, name: str) -> str:
        category = normalize_category(name)
        if category in self.categories():
            raise ValidationError(
                f"이미 등록된 카테고리입니다: {category}", "category list 로 확인하세요."
            )
        self.data.categories.append({"name": category})
        return category

    def count_by_category(self, name: str) -> int:
        return sum(1 for tx in self._transactions() if tx.category == name)

    def remove_category(self, name: str, replace_with: str | None = None) -> int:
        """카테고리를 지운다. 사용 중이면 대체 카테고리로 옮긴 뒤 지운다.

        거래를 먼저 커밋하고 카테고리를 나중에 지운다. 두 파일을 한 번에 바꿀
        수는 없으므로, 중간에 실패해도 참조가 깨지지 않는 방향을 택한다.
        중간 실패 시 쓰이지 않는 카테고리가 남을 뿐이다.
        """
        category = normalize_category(name)
        if category not in self.categories():
            raise NotFoundError(
                f"등록되지 않은 카테고리입니다: {category}", "category list 로 확인하세요."
            )

        used = self.count_by_category(category)
        if used and replace_with is None:
            raise ValidationError(
                f"'{category}' 를 사용하는 거래가 {used}건 있습니다.",
                "--replace-with <카테고리> 로 대체할 카테고리를 지정하세요.",
            )

        if used:
            target = self.require_category(str(replace_with))
            if target == category:
                raise ValidationError(
                    "대체 카테고리가 삭제할 카테고리와 같습니다.",
                    "다른 카테고리를 지정하세요.",
                )

            def transform(row: dict[str, Any]) -> dict[str, Any]:
                if row.get("category") != category:
                    return row
                return {**row, "category": target}

            self._rewrite(transform)

        self.data.categories.write_all(
            {"name": item} for item in self.categories() if item != category
        )
        return used
