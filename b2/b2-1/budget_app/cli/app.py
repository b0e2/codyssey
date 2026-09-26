"""명령 핸들러와 디스패처.

파서 정의는 `parser.py` 에 있다. 여기서는 파싱된 인자를 도메인 값으로
바꿔 서비스에 넘기고, 결과를 화면에 쓰는 일만 한다.
"""

from __future__ import annotations

from argparse import Namespace

from budget_app.cli.parser import build_parser
from budget_app.cli.prompts import ask, parse_day, require_text
from budget_app.cli.render import (
    format_amount,
    print_transactions,
    render_lines,
    render_table,
    warn,
)
from budget_app.decorators import Handler, as_command
from budget_app.errors import AppError, ValidationError
from budget_app.validators import (
    normalize_category,
    parse_amount,
    parse_date,
    parse_tags,
    parse_type,
)
from budget_app.models import Context, Query, Transaction
from budget_app.service.categories import Categories
from budget_app.service.ledger import Ledger, open_ledger
from budget_app.service.porting import Porting
from budget_app.service.recurring import Recurring
from budget_app.service.reports import Reports


# ── 공통 ──────────────────────────────────────────────────────────────────



def _open_ledger(ctx: Context) -> Ledger:
    ledger, seeded = open_ledger(ctx.data_dir)
    if seeded:
        warn(
            "[안내] 데이터 디렉터리를 만들고 기본 카테고리를 등록했습니다: "
            + ", ".join(seeded)
        )
    return ledger


def _build_query(args: Namespace) -> Query:
    return Query(
        date_from=parse_date(args.date_from) if args.date_from else None,
        date_to=parse_date(args.date_to) if args.date_to else None,
        category=normalize_category(args.category) if args.category else None,
        type=args.type,
        keyword=args.keyword,
        tag=args.tag,
    )


# ── 명령 ──────────────────────────────────────────────────────────────────


@as_command
def cmd_add(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)
    date = ask("날짜(YYYY-MM-DD)", parse_date)
    tx_type = ask("타입(income/expense)", parse_type)
    category = ask("카테고리", ledger.require_category)
    amount = ask("금액(양수)", parse_amount)
    memo = ask("메모(선택)", lambda raw: raw.strip(), optional=True)
    tags = ask("태그(쉼표로 구분, 없으면 엔터)", parse_tags, optional=True)

    tx = ledger.create(
        date=date, type=tx_type, category=category, amount=amount, memo=memo, tags=tags
    )
    print(f"[저장 완료] id={tx.id}")
    return 0


@as_command
def cmd_list(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)
    rows = ledger.search(Query(), args.limit)
    print_transactions(rows)
    return 0


@as_command
def cmd_search(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)
    rows = ledger.search(_build_query(args), args.limit)
    print_transactions(rows)
    return 0


@as_command
def cmd_update(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)
    changes: dict[str, object] = {}
    # 옵션을 아예 주지 않은 것과 빈 문자열로 지운 것을 구분해야 하므로 None 으로만 거른다.
    if args.date is not None:
        changes["date"] = parse_date(args.date)
    if args.type is not None:
        changes["type"] = parse_type(args.type)
    if args.category is not None:
        changes["category"] = args.category
    if args.amount is not None:
        changes["amount"] = parse_amount(args.amount)
    if args.memo is not None:
        changes["memo"] = args.memo.strip()
    if args.tags is not None:
        changes["tags"] = parse_tags(args.tags)

    tx = ledger.update(args.tx_id, changes)
    print(f"[수정 완료] id={tx.id}")
    print_transactions([tx])
    return 0


@as_command
def cmd_delete(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)
    tx = ledger.delete(args.tx_id)
    print(f"[삭제 완료] id={tx.id} {tx.date.isoformat()} {tx.category} {format_amount(tx.amount)}")
    return 0


@as_command
def cmd_category(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)

    if args.action == "list":
        categories = ledger.categories()
        if not categories:
            print("[안내] 등록된 카테고리가 없습니다.")
            return 0
        print(render_lines(categories))
        return 0

    if args.action == "add":
        name = ask("카테고리명", Categories(ledger).add)
        print(f"[저장 완료] category={name}")
        return 0

    moved = Categories(ledger).remove(args.name, args.replace_with)
    if moved:
        print(f"[삭제 완료] category={args.name} (거래 {moved}건을 {args.replace_with} 로 옮김)")
    else:
        print(f"[삭제 완료] category={args.name}")
    return 0


@as_command
def cmd_budget(ctx: Context, args: Namespace) -> int:
    reports = Reports(_open_ledger(ctx))

    if args.action == "set":
        budget = reports.set_budget(args.month, args.amount)
        print(f"[저장 완료] {budget.month} 예산 {format_amount(budget.amount)}원")
        return 0

    budgets = reports.budgets()
    if not budgets:
        print("[안내] 설정된 예산이 없습니다.")
        return 0
    print(
        render_table(
            ("월", "예산"),
            [[b.month, format_amount(b.amount)] for b in budgets],
            ("left", "right"),
        )
    )
    return 0


@as_command
def cmd_summary(ctx: Context, args: Namespace) -> int:
    if args.top <= 0:
        # 데이터 유무와 관계없이 같은 입력은 같게 판정해야 한다.
        raise ValidationError("--top 은 1 이상이어야 합니다.", f"입력값: {args.top}")

    ledger = _open_ledger(ctx)
    summary = Reports(ledger).summarize(args.month)

    if summary.is_empty:
        # 유효한 달을 정상 조회했고 거래가 없을 뿐이므로 오류가 아니다.
        print(f"[안내] {summary.month} 데이터가 없습니다.")
        return 0

    print(f"총 수입: {format_amount(summary.total_income)}원")
    print(f"총 지출: {format_amount(summary.total_expense)}원")
    print(f"잔액: {format_amount(summary.balance)}원")

    if summary.budget is None:
        print("예산: 미설정")
    else:
        print(
            f"예산: {format_amount(summary.budget)}원 "
            f"(사용률 {summary.usage_rate:.1f}%)"
        )
        if summary.is_over_budget:
            over = summary.total_expense - summary.budget
            print(f"[경고] 예산을 {format_amount(over)}원 초과했습니다.")

    top = summary.top_expenses(args.top)
    if top:
        print(f"\n지출 TOP {len(top)}")
        for rank, (category, amount) in enumerate(top, start=1):
            print(f"{rank}) {category} {format_amount(amount)}원")
    return 0


@as_command
def cmd_export(ctx: Context, args: Namespace) -> int:
    if args.month and (args.date_from or args.date_to):
        raise ValidationError(
            "--month 와 --from/--to 는 함께 쓸 수 없습니다.",
            "둘 중 하나만 지정하세요.",
        )
    if not args.month and not (args.date_from and args.date_to):
        # 한쪽만 주면 열린 구간이 되어 의도보다 훨씬 많은 데이터가 나간다.
        raise ValidationError(
            "기간 조건이 필요합니다.",
            "--month YYYY-MM 또는 --from YYYY-MM-DD --to YYYY-MM-DD 를 지정하세요.",
        )

    ledger = _open_ledger(ctx)
    query = (
        Query.for_month(args.month)
        if args.month
        else Query(
            date_from=parse_date(args.date_from) if args.date_from else None,
            date_to=parse_date(args.date_to) if args.date_to else None,
        )
    )
    count = Porting(ledger).export(query, args.out)
    print(f"[완료] {args.out} ({count} records)")
    return 0


@as_command
def cmd_import(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)
    result = Porting(ledger).import_csv(args.src)
    detail = f" (상세: {result.errors_path})" if result.errors_path else ""
    print(f"[완료] imported={result.imported}, skipped={result.skipped}{detail}")
    return 0


@as_command
def cmd_backup(ctx: Context, args: Namespace) -> int:
    dest = Porting(_open_ledger(ctx)).backup()
    print(f"[백업 완료] {dest}")
    return 0


@as_command
def cmd_repair(ctx: Context, args: Namespace) -> int:
    report = Porting(_open_ledger(ctx)).repair()
    if not report.moved:
        print("[안내] 정리할 행이 없습니다.")
        return 0
    for name, count in sorted(report.moved.items()):
        print(f"{name}: {count}행 격리")
    print(f"[완료] {report.total}행을 {report.destination} 로 옮겼습니다.")
    return 0


@as_command
def cmd_recurring(ctx: Context, args: Namespace) -> int:
    ledger = _open_ledger(ctx)
    recurring = Recurring(ledger)
    actions = {
        "list": _recurring_list,
        "add": _recurring_add,
        "remove": _recurring_remove,
        "apply": _recurring_apply,
    }
    return actions[args.action](recurring, ledger, args)


def _recurring_list(recurring: Recurring, ledger: Ledger, args: Namespace) -> int:
    rules = recurring.rules()
    if not rules:
        print("[안내] 등록된 반복 규칙이 없습니다.")
        return 0
    print(
        render_table(
            ("id", "이름", "일자", "타입", "카테고리", "금액"),
            [
                [r.id, r.name, str(r.day), r.type, r.category, format_amount(r.amount)]
                for r in rules
            ],
            ("left", "left", "right", "left", "left", "right"),
        )
    )
    return 0


def _recurring_add(recurring: Recurring, ledger: Ledger, args: Namespace) -> int:
    rule = recurring.create(
        name=ask("규칙 이름", require_text("규칙 이름")),
        day=ask("일자(1-31)", parse_day),
        type=ask("타입(income/expense)", parse_type),
        category=ask("카테고리", ledger.require_category),
        amount=ask("금액(양수)", parse_amount),
        memo=ask("메모(선택)", lambda raw: raw.strip(), optional=True),
        tags=ask("태그(쉼표로 구분, 없으면 엔터)", parse_tags, optional=True),
    )
    print(f"[저장 완료] id={rule.id} {rule.name} 매월 {rule.day}일")
    return 0


def _recurring_remove(recurring: Recurring, ledger: Ledger, args: Namespace) -> int:
    rule = recurring.remove(args.rule_id)
    print(f"[삭제 완료] id={rule.id} {rule.name}")
    return 0


def _recurring_apply(recurring: Recurring, ledger: Ledger, args: Namespace) -> int:
    created = recurring.apply(args.month)
    # 건너뛴 규칙을 알리지 않으면 "생성할 내역이 없다"와 구분되지 않는다.
    warn(*recurring.warnings)
    if not created:
        print(f"[안내] {args.month} 에 새로 생성할 반복 내역이 없습니다.")
        return 0
    print(f"[완료] {args.month} 반복 내역 {len(created)}건 생성")
    print_transactions(created)
    return 0




@as_command
def _unimplemented(ctx: Context, args: Namespace) -> int:
    raise AppError(
        f"'{args.command}' 명령은 아직 구현되지 않았습니다.",
        "python -m budget_app --help 로 사용 가능한 명령을 확인하세요.",
    )


HANDLERS: dict[str, Handler] = {
    "add": cmd_add,
    "list": cmd_list,
    "search": cmd_search,
    "update": cmd_update,
    "delete": cmd_delete,
    "category": cmd_category,
    "budget": cmd_budget,
    "summary": cmd_summary,
    "export": cmd_export,
    "import": cmd_import,
    "backup": cmd_backup,
    "repair": cmd_repair,
    "recurring": cmd_recurring,
}


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
