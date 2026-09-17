"""저장된 행을 도메인 객체로 읽는 공통 경로.

읽는 기준이 한 곳에 있다. 저장 파일마다 따로 두면 파일마다 기준이 달라진다.
읽을 수 없는 행을 만나면 멈추고, 어느 파일의 무엇이 문제인지 알린다.
"""

from __future__ import annotations

from typing import Any, Callable, Iterator, TypeVar

from budget_app.models import StorageError, ValidationError
from budget_app.storage import JsonlStore

T = TypeVar("T")


def read(
    store: JsonlStore, build: Callable[[dict[str, Any]], T], *, label: str
) -> Iterator[T]:
    """행을 하나씩 도메인 객체로 만들어 흘린다."""
    for row in store.stream():
        try:
            yield build(row)
        except ValidationError as exc:
            raise StorageError(
                f"저장된 {label}을(를) 읽을 수 없습니다: {exc.message}",
                "repair 명령으로 정리하거나 해당 줄을 고친 뒤 다시 실행하세요.",
            ) from None
