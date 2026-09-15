"""CSV 가져오기·내보내기.

저장은 JSONL 이지만 교환은 CSV 로 한다. 스프레드시트와 주고받으려면
사람이 열어볼 수 있는 포맷이 필요하고, 그 대신 태그 배열 같은 구조는
문자열로 눌러 담는다.
"""

from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from budget_app.models import (
    AppError,
    Query,
    StorageError,
    Transaction,
    ValidationError,
    format_tx_id,
    parse_amount,
    parse_date,
    parse_tags,
    parse_type,
)
from budget_app.service.ledger import Ledger

CSV_COLUMNS = ("date", "type", "category", "amount", "memo", "tags")
REQUIRED_COLUMNS = ("date", "type", "category", "amount")


@dataclass
class ImportResult:
    imported: int = 0
    skipped: int = 0
    errors_path: Path | None = None
    failures: list[tuple[int, str]] = field(default_factory=list)


class Porting:
    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger
        self.data = ledger.data

    # ── 내보내기 ────────────────────────────────────────────────────────

    def export(self, query: Query, out: Path) -> int:
        """조건에 맞는 거래를 CSV 로 저장한다.

        날짜 오름차순으로 쓴다. 다시 가져올 때 저장 순서와 날짜 순서가 같아져
        번호가 뒤섞이지 않는다. 정렬 때문에 대상 건수만큼 메모리를 쓴다.
        """
        if self.data.is_managed(out):
            raise ValidationError(
                f"저장 파일을 내보내기 대상으로 쓸 수 없습니다: {out}",
                "다른 경로를 지정하세요. 운영 데이터가 CSV 로 덮어써집니다.",
            )
        rows = sorted(
            (tx for tx in self.ledger.stream_transactions() if query.matches(tx)),
            key=lambda tx: (tx.date, tx.seq),
        )
        self._write_csv(out, rows)
        return len(rows)

    def _write_csv(self, out: Path, rows: list[Transaction]) -> None:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=out.parent,
            prefix=f".{out.name}.",
            suffix=".tmp",
            delete=False,
        )
        try:
            with tmp:
                writer = csv.DictWriter(tmp, fieldnames=list(CSV_COLUMNS))
                writer.writeheader()
                for tx in rows:
                    writer.writerow(
                        {
                            "date": tx.date.isoformat(),
                            "type": tx.type,
                            "category": tx.category,
                            "amount": tx.amount,
                            "memo": tx.memo,
                            # 쉼표 구분을 그대로 쓰고 값은 csv 모듈이 인용해 준다.
                            "tags": ",".join(tx.tags),
                        }
                    )
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp.name, out)
        except BaseException:
            Path(tmp.name).unlink(missing_ok=True)
            raise

    # ── 가져오기 ────────────────────────────────────────────────────────

    def import_csv(self, src: Path) -> ImportResult:
        """행 단위로 검증해 정상 행만 반영한다.

        깨진 행 하나 때문에 전체를 버리면 사용자가 원인을 찾기 어렵다.
        대신 실패한 행은 이유와 함께 별도 CSV 로 남긴다.

        반영은 한 번의 교체로 끝낸다. 행마다 덧붙이면 중간에 실패했을 때
        얼마나 들어갔는지 알 수 없다.
        """
        if not src.exists():
            raise StorageError(
                f"파일을 찾을 수 없습니다: {src}", "경로를 확인하세요."
            )

        result = ImportResult()
        prepared: list[dict[str, Any]] = []
        categories = set(self.ledger.categories())
        next_seq = int(self.ledger.next_id()[3:])

        with src.open(encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp)
            self._check_header(src, reader.fieldnames)
            for line_no, row in enumerate(reader, start=2):  # 1행은 헤더
                try:
                    tx = self._to_transaction(row, categories, next_seq)
                except AppError as exc:
                    result.skipped += 1
                    result.failures.append((line_no, exc.message))
                    continue
                prepared.append(tx.to_dict())
                next_seq += 1

        if result.failures:
            result.errors_path = self._write_failures(src, result.failures)

        if prepared:
            store = self.data.transactions
            store.write_all(self._chain(store.stream_strict(), prepared))
        result.imported = len(prepared)
        return result

    @staticmethod
    def _chain(existing: Iterator[dict[str, Any]], new_rows: list[dict[str, Any]]):
        yield from existing
        yield from new_rows

    def _check_header(self, src: Path, fieldnames: list[str] | None) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in (fieldnames or [])]
        if missing:
            raise ValidationError(
                f"CSV 머리글에 필수 열이 없습니다: {', '.join(missing)}",
                f"필요한 열: {', '.join(CSV_COLUMNS)}",
            )

    def _to_transaction(
        self, row: dict[str, Any], categories: set[str], seq: int
    ) -> Transaction:
        category = str(row.get("category") or "").strip()
        if category not in categories:
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {category or '(비어 있음)'}"
            )
        return Transaction(
            id=format_tx_id(seq),
            type=parse_type(str(row.get("type") or "")),
            date=parse_date(str(row.get("date") or "")),
            amount=parse_amount(str(row.get("amount") or "")),
            category=category,
            memo=str(row.get("memo") or "").strip(),
            tags=parse_tags(str(row.get("tags") or "")),
        )

    @staticmethod
    def _write_failures(src: Path, failures: list[tuple[int, str]]) -> Path:
        path = src.with_name(src.name + ".errors.csv")
        with path.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(("line_no", "reason"))
            writer.writerows(failures)
        return path

    # ── 백업 ────────────────────────────────────────────────────────────

    def backup(self) -> Path:
        """저장 파일을 타임스탬프 디렉터리에 복사한다.

        파싱하지 않고 바이트 그대로 옮긴다. 손상된 파일이라도 원본 그대로
        남겨야 나중에 손으로 고칠 수 있다.
        """
        return self.data.backup()
