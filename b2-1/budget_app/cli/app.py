"""명령행 파서와 디스패처.

파서 정의는 여기서 완결하고, 각 명령의 동작은 구현 단계에서 붙인다.
"""

from __future__ import annotations

import argparse
from argparse import Namespace
from pathlib import Path

from budget_app.decorators import Handler, as_command
from budget_app.models import AppError, Context

DEFAULT_DATA_DIR = "./data"
DEFAULT_LIST_LIMIT = 20
DEFAULT_TOP = 3


def _global_options(*, suppress: bool) -> argparse.ArgumentParser:
    """모든 명령이 공유하는 옵션.

    부모 파서로 붙여 `budget_app --verbose list` 와 `budget_app list --verbose`
    를 모두 허용한다.

    서브파서에 붙일 때는 기본값을 SUPPRESS로 둔다. 기본값을 그대로 두면
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


def build_parser() -> argparse.ArgumentParser:
    common = _global_options(suppress=True)
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="콘솔 가계부",
        parents=[_global_options(suppress=False)],
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    sub.add_parser("add", parents=[common], help="거래 추가 (대화형)")

    p_list = sub.add_parser("list", parents=[common], help="거래 목록 (최신순)")
    p_list.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIST_LIMIT,
        help=f"출력 건수 (기본: {DEFAULT_LIST_LIMIT})",
    )

    p_search = sub.add_parser("search", parents=[common], help="조건 검색")
    p_search.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD", help="시작일 (포함)")
    p_search.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD", help="종료일 (포함)")
    p_search.add_argument("--category", help="카테고리")
    p_search.add_argument("--type", choices=("income", "expense"), help="거래 타입")
    p_search.add_argument("--q", dest="keyword", help="메모 키워드")
    p_search.add_argument("--tag", help="태그")
    p_search.add_argument("--limit", type=int, default=DEFAULT_LIST_LIMIT, help="출력 건수")

    p_summary = sub.add_parser("summary", parents=[common], help="월별 요약")
    p_summary.add_argument("--month", required=True, metavar="YYYY-MM", help="대상 월")
    p_summary.add_argument(
        "--top", type=int, default=DEFAULT_TOP, help=f"지출 상위 N개 (기본: {DEFAULT_TOP})"
    )

    p_budget = sub.add_parser("budget", parents=[common], help="예산 설정·조회")
    p_budget.set_defaults(group_parser=p_budget)
    budget_sub = p_budget.add_subparsers(dest="action", metavar="<action>")
    p_budget_set = budget_sub.add_parser("set", parents=[common], help="월 예산 저장")
    p_budget_set.add_argument("--month", required=True, metavar="YYYY-MM")
    p_budget_set.add_argument("--amount", required=True, type=int, help="예산 (양수)")
    budget_sub.add_parser("list", parents=[common], help="예산 목록")

    p_category = sub.add_parser("category", parents=[common], help="카테고리 관리")
    p_category.set_defaults(group_parser=p_category)
    category_sub = p_category.add_subparsers(dest="action", metavar="<action>")
    category_sub.add_parser("add", parents=[common], help="카테고리 추가 (대화형)")
    category_sub.add_parser("list", parents=[common], help="카테고리 목록")
    p_category_remove = category_sub.add_parser("remove", parents=[common], help="카테고리 삭제")
    p_category_remove.add_argument("--name", required=True, help="삭제할 카테고리")
    p_category_remove.add_argument(
        "--replace-with", help="사용 중인 경우 대체할 카테고리"
    )

    p_update = sub.add_parser("update", parents=[common], help="거래 수정")
    p_update.add_argument("--id", dest="tx_id", required=True, help="거래 id")
    p_update.add_argument("--date", metavar="YYYY-MM-DD")
    p_update.add_argument("--type", choices=("income", "expense"))
    p_update.add_argument("--category")
    p_update.add_argument("--amount", type=int)
    p_update.add_argument("--memo", help='빈 문자열("")이면 메모를 지운다')
    p_update.add_argument("--tags", help='쉼표 구분. 빈 문자열("")이면 태그를 지운다')

    p_delete = sub.add_parser("delete", parents=[common], help="거래 삭제")
    p_delete.add_argument("--id", dest="tx_id", required=True, help="거래 id")

    p_export = sub.add_parser("export", parents=[common], help="CSV 내보내기")
    p_export.add_argument("--out", required=True, type=Path, help="출력 CSV 경로")
    p_export.add_argument("--month", metavar="YYYY-MM")
    p_export.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD")
    p_export.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD")

    p_import = sub.add_parser("import", parents=[common], help="CSV 가져오기")
    p_import.add_argument("--from", dest="src", required=True, type=Path, help="입력 CSV 경로")

    sub.add_parser("backup", parents=[common], help="데이터 파일 백업")

    p_recurring = sub.add_parser("recurring", parents=[common], help="반복 내역 관리")
    p_recurring.set_defaults(group_parser=p_recurring)
    recurring_sub = p_recurring.add_subparsers(dest="action", metavar="<action>")
    recurring_sub.add_parser("add", parents=[common], help="반복 규칙 추가 (대화형)")
    recurring_sub.add_parser("list", parents=[common], help="반복 규칙 목록")
    p_recurring_remove = recurring_sub.add_parser("remove", parents=[common], help="반복 규칙 삭제")
    p_recurring_remove.add_argument("--id", dest="rule_id", required=True, help="규칙 id")
    p_recurring_apply = recurring_sub.add_parser("apply", parents=[common], help="해당 월에 적용")
    p_recurring_apply.add_argument("--month", required=True, metavar="YYYY-MM")

    return parser


@as_command
def _unimplemented(ctx: Context, args: Namespace) -> int:
    raise AppError(
        f"'{args.command}' 명령은 아직 구현되지 않았습니다.",
        "python -m budget_app --help 로 사용 가능한 명령을 확인하세요.",
    )


HANDLERS: dict[str, Handler] = {}


def dispatch(ctx: Context, args: Namespace) -> int:
    return HANDLERS.get(args.command, _unimplemented)(ctx, args)


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 2

    group_parser = getattr(args, "group_parser", None)
    if group_parser is not None and getattr(args, "action", None) is None:
        group_parser.print_help()
        return 2

    ctx = Context(data_dir=args.data_dir, verbose=args.verbose)
    return dispatch(ctx, args)
