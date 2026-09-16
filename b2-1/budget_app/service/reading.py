"""저장된 행을 도메인 객체로 읽는 공통 경로.

손상 행 정책을 한 곳에만 둔다. 저장 파일마다 따로 구현하면 정책이 갈라진다.
실제로 예산·반복 규칙·카테고리가 거래와 다르게 동작해, 파일을 다시 쓸 때
읽지 못한 행을 지우는 결함이 있었다.

- 조회: 손상 행을 건너뛰고 줄 번호를 모아 경고로 알린다
- 재작성: 첫 손상 행에서 멈춘다. 건너뛴 채 저장하면 원본이 사라진다
"""

from __future__ import annotations

from typing import Any, Callable, Iterator, TypeVar

from budget_app.models import StorageError, ValidationError
from budget_app.storage import JsonlStore, describe_corruption

T = TypeVar("T")


def read(
    store: JsonlStore,
    build: Callable[[dict[str, Any]], T],
    *,
    label: str,
    strict: bool = False,
    warnings: list[str] | None = None,
) -> Iterator[T]:
    """행을 하나씩 도메인 객체로 만들어 흘린다.

    경고는 끝까지 소비했을 때 붙는다. 중간에 멈추면 아직 보지 않은 행이
    손상됐는지 알 수 없으므로 알릴 것도 없다.
    """
    if strict:
        yield from _read_strict(store, build, label)
        return

    corrupt: list[int] = []
    for line_no, row in store.stream_numbered(corrupt):
        try:
            yield build(row)
        except ValidationError:
            corrupt.append(line_no)
    if corrupt and warnings is not None:
        warnings.append(describe_corruption(store.path, sorted(corrupt)))


def _read_strict(
    store: JsonlStore, build: Callable[[dict[str, Any]], T], label: str
) -> Iterator[T]:
    for row in store.stream_strict():
        try:
            yield build(row)
        except ValidationError as exc:
            raise StorageError(
                f"저장된 {label}을(를) 읽을 수 없습니다: {exc.message}",
                f"{store.path} 를 확인하세요.",
            ) from None
