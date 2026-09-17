"""JSONL 파일 저장소.

이 계층은 도메인 규칙을 모른다. dict 를 읽고 쓸 뿐이며, `models` 에서 가져오는
것은 예외 계층뿐이다. 거래인지 예산인지는 호출자가 안다.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from budget_app.models import StorageError

DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")
_TAIL_BLOCK = 4096


@contextmanager
def io_guard(path: Path, action: str = "처리"):
    """파일 작업 실패를 저장소 오류로 분류한다.

    그대로 두면 예상치 못한 내부 오류(1)로 새어 나가, 파일 문제인데도
    종료 코드가 문서와 달라진다. 인코딩 오류도 같은 부류로 본다.
    """
    try:
        yield
    except StorageError:
        raise
    except UnicodeDecodeError:
        raise StorageError(
            f"파일이 UTF-8 이 아닙니다: {path}",
            "UTF-8 로 저장한 파일인지 확인하세요.",
        ) from None
    except OSError as exc:
        raise StorageError(
            f"파일을 {action}할 수 없습니다: {path}",
            f"경로와 권한을 확인하세요 ({exc.strerror}).",
        ) from None


@contextmanager
def _reading(path: Path):
    with io_guard(path, "읽기"):
        fp = path.open(encoding="utf-8")
        try:
            yield fp
        finally:
            fp.close()


@dataclass(frozen=True)
class JsonlStore:
    """한 JSONL 파일에 대한 읽기·쓰기.

    저장 파일마다 클래스를 나누지 않는다. 파일 간 차이는 경로뿐이고 동작은 같다.
    """

    path: Path

    # ── 읽기 ────────────────────────────────────────────────────────────

    def stream(self) -> Iterator[dict[str, Any]]:
        """행을 하나씩 흘린다. 파일 전체를 메모리에 올리지 않는다.

        읽을 수 없는 행을 만나면 멈춘다. 조회든 재작성이든 같은 기준이라,
        일부만 보여주거나 일부만 저장하는 상태가 생기지 않는다.
        """
        if not self.path.exists():
            return
        with _reading(self.path) as fp:
            for line_no, line in enumerate(fp, start=1):
                text = line.strip()
                if not text:
                    continue
                yield self._decode(line_no, text)

    def iter_lines(self) -> Iterator[tuple[int, str]]:
        """줄 번호와 원문. 복구 명령이 손상 행을 그대로 옮길 때 쓴다."""
        if not self.path.exists():
            return
        with _reading(self.path) as fp:
            for line_no, line in enumerate(fp, start=1):
                text = line.strip()
                if text:
                    yield line_no, text

    def _decode(self, line_no: int, text: str) -> dict[str, Any]:
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            row = None
        if not isinstance(row, dict):
            raise StorageError(
                f"{self.path.name} 의 {line_no}번째 줄을 읽을 수 없습니다.",
                f"repair 명령으로 정리하거나 해당 줄을 고친 뒤 다시 실행하세요.",
            )
        return row

    def last_row(self) -> dict[str, Any] | None:
        """마지막 행. 파일 크기와 무관하게 끝에서부터만 읽는다.

        거래 id 채번이 전체 스캔 없이 끝나도록 하기 위한 것이다.
        """
        with io_guard(self.path, "읽기"):
            if not self.path.exists() or self.path.stat().st_size == 0:
                return None
            text = self._last_nonempty_line()
        if text is None:
            return None
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            raise StorageError(
                f"{self.path.name} 의 마지막 행이 손상되어 이어쓸 수 없습니다.",
                "해당 줄을 고치거나 삭제한 뒤 다시 실행하세요.",
            ) from None
        if not isinstance(row, dict):
            raise StorageError(
                f"{self.path.name} 의 마지막 행이 손상되어 이어쓸 수 없습니다.",
                "해당 줄을 고치거나 삭제한 뒤 다시 실행하세요.",
            )
        return row

    def _last_nonempty_line(self) -> str | None:
        with self.path.open("rb") as fp:
            fp.seek(0, io.SEEK_END)
            end = fp.tell()
            buffer = b""
            while end > 0:
                size = min(_TAIL_BLOCK, end)
                end -= size
                fp.seek(end)
                buffer = fp.read(size) + buffer
                lines = [ln for ln in buffer.split(b"\n") if ln.strip()]
                # 첫 줄은 앞 블록에서 잘렸을 수 있으므로 두 줄 이상 모였을 때만 확정한다.
                if len(lines) >= 2 or end == 0:
                    if not lines:
                        return None
                    return lines[-1].decode("utf-8")
        return None

    # ── 쓰기 ────────────────────────────────────────────────────────────

    def append(self, row: dict[str, Any]) -> None:
        """한 행을 덧붙인다. 기존 내용을 다시 쓰지 않으므로 파일 크기와 무관하다.

        손상 행 전수 검사는 하지 않는다. 다만 마지막 행이 개행 없이 끝났다면
        새 JSON 이 그 행에 이어붙어 두 행이 함께 깨지므로, 그 경우만 막는다.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self._ends_with_newline():
            raise StorageError(
                f"{self.path.name} 의 마지막 행이 완결되지 않아 이어쓸 수 없습니다.",
                "파일 끝에 줄바꿈을 넣거나 깨진 줄을 정리한 뒤 다시 실행하세요.",
            )
        try:
            with self.path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError as exc:
            raise StorageError(
                f"파일에 쓸 수 없습니다: {self.path}",
                f"경로와 권한을 확인하세요 ({exc.strerror}).",
            ) from None

    def _ends_with_newline(self) -> bool:
        with io_guard(self.path, "읽기"):
            if not self.path.exists() or self.path.stat().st_size == 0:
                return True
            with self.path.open("rb") as fp:
                fp.seek(-1, io.SEEK_END)
                return fp.read(1) == b"\n"

    def write_all(self, rows: Iterable[dict[str, Any]]) -> int:
        """파일 내용을 통째로 교체한다.

        임시 파일에 전부 쓰고 fsync 한 뒤 os.replace 로 바꾼다. 중간에 실패하면
        임시 파일만 버려지고 원본은 그대로 남는다.
        """
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                f"디렉터리를 만들 수 없습니다: {self.path.parent}",
                f"경로와 권한을 확인하세요 ({exc.strerror}).",
            ) from None
        with io_guard(self.path, "저장"):
            tmp = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            )
        written = 0
        try:
            with tmp:
                for row in rows:
                    tmp.write(json.dumps(row, ensure_ascii=False) + "\n")
                    written += 1
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp.name, self.path)
        except OSError as exc:
            Path(tmp.name).unlink(missing_ok=True)
            raise StorageError(
                f"파일을 저장할 수 없습니다: {self.path}",
                f"경로와 권한을 확인하세요 ({exc.strerror}).",
            ) from None
        except BaseException:
            Path(tmp.name).unlink(missing_ok=True)
            raise
        self._fsync_dir()
        return written

    def rewrite(self, transform: Callable[[dict[str, Any]], dict[str, Any] | None]) -> int:
        """모든 행에 `transform` 을 적용해 다시 쓴다. None 을 돌려준 행은 삭제된다."""
        return self.write_all(
            row for row in map(transform, self.stream()) if row is not None
        )

    def _fsync_dir(self) -> None:
        try:
            fd = os.open(self.path.parent, os.O_RDONLY)
        except OSError:
            return  # 디렉터리 fsync 는 최선 노력이다. 교체 자체는 이미 끝났다.
        try:
            os.fsync(fd)
        except OSError:
            pass  # 일부 파일시스템은 디렉터리 fsync 를 지원하지 않는다
        finally:
            os.close(fd)

    def copy_to(self, dest_dir: Path) -> Path | None:
        """백업용 복사. 파싱하지 않고 바이트 그대로 옮긴다."""
        with io_guard(dest_dir, "복사"):
            if not self.path.exists():
                return None
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / self.path.name
            shutil.copy2(self.path, dest)
            return dest


@dataclass(frozen=True)
class DataDir:
    """데이터 디렉터리와 그 안의 저장 파일들."""

    root: Path

    @property
    def transactions(self) -> JsonlStore:
        return JsonlStore(self.root / "transactions.jsonl")

    @property
    def categories(self) -> JsonlStore:
        return JsonlStore(self.root / "categories.jsonl")

    @property
    def budgets(self) -> JsonlStore:
        return JsonlStore(self.root / "budgets.jsonl")

    @property
    def recurring(self) -> JsonlStore:
        return JsonlStore(self.root / "recurring.jsonl")

    @property
    def stores(self) -> tuple[JsonlStore, ...]:
        return (self.transactions, self.categories, self.budgets, self.recurring)

    def ensure(self) -> bool:
        """없으면 만들고 기본 카테고리를 넣는다. 시드를 넣었으면 True.

        시드는 카테고리 파일을 **이번에 새로 만들었을 때만** 넣는다.
        "읽을 수 있는 행이 없으면 시드"로 두면 손상된 파일이 기본값으로
        덮어써지고, 사용자가 카테고리를 모두 지워도 다음 실행에서 되살아난다.
        조회나 백업처럼 읽기만 해야 하는 명령도 이 경로를 지나간다.
        """
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            seeded = not self.categories.path.exists()
            for store in self.stores:
                if not store.path.exists():
                    store.path.touch()
        except OSError as exc:
            raise StorageError(
                f"데이터 디렉터리를 준비할 수 없습니다: {self.root}",
                f"경로와 권한을 확인하세요 ({exc.strerror}).",
            ) from None
        if seeded:
            self.categories.write_all({"name": name} for name in DEFAULT_CATEGORIES)
        return seeded

    def is_managed(self, path: Path) -> bool:
        """저장소가 관리하는 파일인지. 내보내기가 운영 데이터를 덮어쓰지 못하게 쓴다."""
        try:
            resolved = path.resolve()
        except OSError:
            return False
        return any(store.path.resolve() == resolved for store in self.stores)

    def quarantine_dir(self, label: str | None = None) -> Path:
        stamp = label or datetime.now().strftime("%Y%m%d-%H%M%S")
        return self.root / "quarantine" / stamp

    def backup(self, label: str | None = None) -> Path:
        """저장 파일을 타임스탬프 디렉터리에 복사한다.

        대상은 저장 파일 넷으로 고정한다. 로그나 기존 백업까지 딸려가지 않게 하고,
        나중에 다른 파일이 생겨도 백업 대상이 저절로 늘지 않게 하려는 것이다.
        """
        stamp = label or datetime.now().strftime("%Y%m%d-%H%M%S")
        with io_guard(self.root / "backups", "생성"):
            dest = self.root / "backups" / stamp
            suffix = 2
            while dest.exists():
                dest = self.root / "backups" / f"{stamp}-{suffix}"
                suffix += 1
            dest.mkdir(parents=True, exist_ok=True)
        for store in self.stores:
            store.copy_to(dest)
        return dest
