"""거래 쓰기 경로와 조회.

저장소가 흘리는 dict 를 도메인 객체로 바꾸고, 업무 규칙을 적용한다.
파일 경로는 알지 못한다.
"""

from __future__ import annotations

import heapq
from dataclasses import replace
from itertools import chain
from pathlib import Path
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
from budget_app.service.reading import read
from budget_app.storage import DataDir


def _category_name(row: dict[str, Any]) -> str:
    name = row.get("name")
    if not isinstance(name, str):
        raise ValidationError("카테고리 이름이 문자열이 아닙니다.")
    return normalize_category(name)


class Ledger:
    """거래 관련 유스케이스.

    명령 하나당 인스턴스 하나를 만든다. 읽는 동안 건너뛴 손상 행 경고를
    `warnings` 에 모아두면 CLI 가 결과와 함께 보여줄 수 있다.
    """

    def __init__(self, data: DataDir) -> None:
        self.data = data
        self.warnings: list[str] = []

    # ── 카테고리 ────────────────────────────────────────────────────────

    def categories(self, strict: bool = False) -> list[str]:
        """카테고리 목록.

        파일을 다시 쓰는 경로에서는 strict 로 읽는다. 손상 행을 건너뛴 채
        저장하면 읽지 못한 카테고리가 사라진다.
        """
        return list(
            read(
                self.data.categories,
                _category_name,
                label="카테고리",
                strict=strict,
                warnings=self.warnings,
            )
        )

    def require_category(self, name: str) -> str:
        category = normalize_category(name)
        if category not in self.categories():
            raise NotFoundError(
                f"등록되지 않은 카테고리입니다: {category}",
                "category list 로 목록을 보거나 category add 로 등록하세요.",
            )
        return category

    # ── 읽기 ────────────────────────────────────────────────────────────

    def stream_transactions(self) -> Iterator[Transaction]:
        """정상 행만 흘린다. 손상 행과 규칙에 어긋난 행은 건너뛰고 경고로 모은다."""
        return read(
            self.data.transactions,
            Transaction.from_dict,
            label="거래",
            warnings=self.warnings,
        )

    def search(self, query: Query, limit: int) -> list[Transaction]:
        """조건에 맞는 거래를 최신순으로 돌려준다.

        정렬이 필요하므로 파일은 끝까지 읽어야 한다. 대신 상위 N개만 들고 있는
        힙을 써서 결과 목록 크기를 limit 으로 묶는다. 파일이 커져도 메모리는
        늘지 않는다.
        """
        if limit <= 0:
            raise ValidationError("--limit 은 1 이상이어야 합니다.", f"입력값: {limit}")
        hits = (tx for tx in self.stream_transactions() if query.matches(tx))
        return heapq.nlargest(limit, hits, key=lambda tx: (tx.date, tx.seq))

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

        모든 행을 모델로 복원한 뒤 넘긴다. JSON 문법만 보면 필수 항목이
        빠졌거나 금액이 0인 행이 그대로 다시 저장되고, 손상 행이 있으면
        중단한다는 약속도 문법 오류에만 적용된다.
        """

        rows = read(
            self.data.transactions, Transaction.from_dict, label="거래", strict=True
        )
        self.data.transactions.write_all(
            row for row in map(transform, rows) if row is not None
        )

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

        def transform(tx: Transaction) -> dict[str, Any]:
            if tx.id != wanted:
                return tx.to_dict()
            # dataclass replace 가 __post_init__ 을 다시 태우므로 변경분도 검증된다.
            new_tx = replace(tx, **changes)
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

        def transform(tx: Transaction) -> dict[str, Any] | None:
            if tx.id != wanted:
                return tx.to_dict()
            removed.append(tx)
            return None

        self._rewrite(transform)
        if not removed:
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {wanted}", "list 로 id 를 확인하세요."
            )
        return removed[0]

    def strict_rows(self) -> Iterator[dict[str, Any]]:
        """저장된 거래를 모델로 검증한 뒤 다시 dict 로 흘린다.

        파일을 통째로 다시 쓰는 경로가 기존 행을 그대로 복사하면, JSON 문법만
        맞고 규칙에 어긋난 행이 새 파일에도 그대로 남는다. 덧붙이는 경로라도
        파일 전체를 다시 쓰는 이상 같은 기준을 적용한다.
        """
        for tx in read(
            self.data.transactions, Transaction.from_dict, label="거래", strict=True
        ):
            yield tx.to_dict()

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
        return sum(1 for tx in self.stream_transactions() if tx.category == name)

    def remove_category(self, name: str, replace_with: str | None = None) -> int:
        """카테고리를 지운다. 사용 중이면 대체 카테고리로 옮긴 뒤 지운다.

        거래를 먼저 커밋하고 카테고리를 나중에 지운다. 두 파일을 한 번에 바꿀
        수는 없으므로, 중간에 실패해도 참조가 깨지지 않는 방향을 택한다.
        중간 실패 시 쓰이지 않는 카테고리가 남을 뿐이다.
        """
        category = normalize_category(name)
        # 카테고리 파일 검사를 먼저 끝낸다. 거래를 옮긴 뒤에 이 파일이 손상된 걸
        # 알게 되면, 명령은 실패했는데 거래만 바뀐 상태로 남는다.
        registered = self.categories(strict=True)
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
        used = self.count_by_category(category)
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

        self._rewrite(transform)
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


    def add_many(self, transactions: list[Transaction]) -> list[Transaction]:
        """여러 거래를 한 번의 교체로 저장한다.

        하나씩 append 하면 중간에 실패했을 때 일부만 남아 다시 실행하기
        어려워진다.
        """
        if not transactions:
            return []
        # 건마다 require_category 를 부르면 카테고리 파일을 건수만큼 읽는다.
        registered = set(self.categories())
        for tx in transactions:
            if tx.category not in registered:
                raise NotFoundError(
                    f"등록되지 않은 카테고리입니다: {tx.category}",
                    "category list 로 목록을 보거나 category add 로 등록하세요.",
                )
        store = self.data.transactions
        rows = [tx.to_dict() for tx in transactions]
        store.write_all(chain(self.strict_rows(), rows))
        return transactions


def open_ledger(data_dir: Path) -> tuple[Ledger, list[str]]:
    """데이터 디렉터리를 준비하고 `Ledger` 를 만든다.

    CLI 가 저장소를 직접 열면 계층이 샌다. 디렉터리 생성과 기본 카테고리
    시드는 업무 규칙이므로 여기서 처리하고, 새로 심은 카테고리만 알려준다.
    """
    data = DataDir(data_dir)
    seeded = data.ensure()
    ledger = Ledger(data)
    return ledger, ledger.categories() if seeded else []
