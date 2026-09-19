"""명령행 파서 정의.

핸들러와 파일을 나눈 이유는 바뀌는 이유가 다르기 때문이다. 파서는 명령이나
옵션이 늘 때 손대고, 핸들러는 동작이 바뀔 때 손댄다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_DATA_DIR = "./data"
DEFAULT_LIST_LIMIT = 20
DEFAULT_TOP = 3

TX_TYPES = ("income", "expense")

_SubParsers = argparse._SubParsersAction  # noqa: SLF001 - argparse 가 공개 별칭을 주지 않는다


# ── 공통 옵션 ──────────────────────────────────────────────────────────────


def _global_options(*, suppress: bool) -> argparse.ArgumentParser:
    """모든 명령이 공유하는 옵션.

    부모 파서로 붙여 `budget_app --verbose list` 와 `budget_app list --verbose`
    를 모두 허용한다.

    서브파서에 붙일 때는 기본값을 SUPPRESS 로 둔다. 기본값을 그대로 두면
    서브파서가 파싱할 때 앞쪽에서 이미 받은 값을 기본값으로 덮어써서
    `--data-dir X list` 가 무시된다.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=argparse.SUPPRESS if suppress else Path(DEFAULT_DATA_DIR),
        help=f"데이터 디렉터리 (기본: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=argparse.SUPPRESS if suppress else False,
        help="실행 시간 등 상세 출력",
    )
    return parser


def _add_month(parser: argparse.ArgumentParser, *, required: bool) -> None:
    parser.add_argument("--month", required=required, metavar="YYYY-MM", help="대상 월")


def _add_period(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD", help="시작일 (포함)")
    parser.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD", help="종료일 (포함)")


def _add_limit(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIST_LIMIT,
        help=f"출력 건수 (기본: {DEFAULT_LIST_LIMIT})",
    )


def _add_tx_id(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--id", dest="tx_id", required=True, metavar="TX-000000", help="거래 id"
    )


def _add_group(
    sub: _SubParsers, name: str, help_text: str, common: argparse.ArgumentParser
) -> tuple[argparse.ArgumentParser, _SubParsers]:
    """하위 동작을 갖는 명령을 만든다.

    파서 자신을 기본값에 심어 두면, 동작 없이 `budget_app category` 만 쳤을 때
    그 명령의 도움말을 그대로 보여줄 수 있다. 별도 매핑을 들고 다닐 필요가 없다.
    """
    group = sub.add_parser(name, parents=[common], help=help_text)
    group.set_defaults(group_parser=group)
    return group, group.add_subparsers(dest="action", metavar="<action>")


# ── 명령 묶음 ──────────────────────────────────────────────────────────────


def _add_transaction_commands(sub: _SubParsers, common: argparse.ArgumentParser) -> None:
    sub.add_parser("add", parents=[common], help="거래 추가 (대화형)")

    listing = sub.add_parser("list", parents=[common], help="거래 목록 (최신순)")
    _add_limit(listing)

    search = sub.add_parser("search", parents=[common], help="조건 검색")
    _add_period(search)
    search.add_argument("--category", help="카테고리")
    search.add_argument("--type", choices=TX_TYPES, help="거래 타입")
    search.add_argument("--q", dest="keyword", help="메모 키워드 (부분 일치)")
    search.add_argument("--tag", help="태그 (정확히 일치)")
    _add_limit(search)

    update = sub.add_parser("update", parents=[common], help="거래 수정")
    _add_tx_id(update)
    update.add_argument("--date", metavar="YYYY-MM-DD")
    update.add_argument("--type", choices=TX_TYPES)
    update.add_argument("--category")
    update.add_argument("--amount", type=int)
    update.add_argument("--memo", help='빈 문자열("")이면 메모를 지운다')
    update.add_argument("--tags", help='쉼표 구분. 빈 문자열("")이면 태그를 지운다')

    delete = sub.add_parser("delete", parents=[common], help="거래 삭제")
    _add_tx_id(delete)


def _add_report_commands(sub: _SubParsers, common: argparse.ArgumentParser) -> None:
    summary = sub.add_parser("summary", parents=[common], help="월별 요약")
    _add_month(summary, required=True)
    summary.add_argument(
        "--top", type=int, default=DEFAULT_TOP, help=f"지출 상위 N개 (기본: {DEFAULT_TOP})"
    )

    _, budget = _add_group(sub, "budget", "예산 설정·조회", common)
    setting = budget.add_parser("set", parents=[common], help="월 예산 저장")
    _add_month(setting, required=True)
    setting.add_argument("--amount", required=True, type=int, help="예산 (양수)")
    budget.add_parser("list", parents=[common], help="예산 목록")


def _add_category_commands(sub: _SubParsers, common: argparse.ArgumentParser) -> None:
    _, category = _add_group(sub, "category", "카테고리 관리", common)
    category.add_parser("add", parents=[common], help="카테고리 추가 (대화형)")
    category.add_parser("list", parents=[common], help="카테고리 목록")
    removal = category.add_parser("remove", parents=[common], help="카테고리 삭제")
    removal.add_argument("--name", required=True, help="삭제할 카테고리")
    removal.add_argument("--replace-with", help="사용 중인 경우 대체할 카테고리")


def _add_porting_commands(sub: _SubParsers, common: argparse.ArgumentParser) -> None:
    export = sub.add_parser("export", parents=[common], help="CSV 내보내기")
    export.add_argument("--out", required=True, type=Path, help="출력 CSV 경로")
    _add_month(export, required=False)
    _add_period(export)

    importing = sub.add_parser("import", parents=[common], help="CSV 가져오기")
    importing.add_argument(
        "--from", dest="src", required=True, type=Path, help="입력 CSV 경로"
    )

    sub.add_parser("backup", parents=[common], help="데이터 파일 백업")
    sub.add_parser("repair", parents=[common], help="읽을 수 없는 행 격리")


def _add_recurring_commands(sub: _SubParsers, common: argparse.ArgumentParser) -> None:
    _, recurring = _add_group(sub, "recurring", "반복 내역 관리", common)
    recurring.add_parser("add", parents=[common], help="반복 규칙 추가 (대화형)")
    recurring.add_parser("list", parents=[common], help="반복 규칙 목록")
    removal = recurring.add_parser("remove", parents=[common], help="반복 규칙 삭제")
    removal.add_argument("--id", dest="rule_id", required=True, help="규칙 id")
    applying = recurring.add_parser("apply", parents=[common], help="해당 월에 적용")
    _add_month(applying, required=True)


# ── 조립 ──────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    common = _global_options(suppress=True)
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="콘솔 가계부",
        parents=[_global_options(suppress=False)],
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    _add_transaction_commands(sub, common)
    _add_report_commands(sub, common)
    _add_category_commands(sub, common)
    _add_porting_commands(sub, common)
    _add_recurring_commands(sub, common)
    return parser
