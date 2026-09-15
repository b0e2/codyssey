"""명령 핸들러의 공통 관심사.

오류 출력·실행 로그·시간 측정은 모든 명령에 똑같이 필요하지만 명령의 일이
아니다. 핸들러마다 반복해 넣는 대신 여기에 한 번만 두고, 정책이 바뀌면
이 파일만 고친다.
"""

from __future__ import annotations

import functools
import sys
import time
import traceback
from argparse import Namespace
from datetime import datetime
from typing import Protocol

from budget_app.models import AppError, Context

_MASKED_FIELDS = ("memo", "tags", "keyword")


class Handler(Protocol):
    """명령 핸들러의 계약.

    핸들러가 `Context` 를 인자로 받는다고 타입으로 선언해 두면, 데코레이터가
    로그 경로나 verbose 를 전역 상태 없이 꺼내 쓸 수 있다. 테스트도 Context 만
    만들어 넘기면 된다.
    """

    def __call__(self, ctx: Context, args: Namespace) -> int: ...


def handle_errors(fn: Handler) -> Handler:
    """예외를 사용자 메시지로 바꾼다.

    스택트레이스는 화면에 내보내지 않고 로그 파일에만 남긴다. 사용자에게는
    원인과 해결 힌트를, 호출한 쪽에는 종료 코드를 준다.
    """

    @functools.wraps(fn)
    def wrapper(ctx: Context, args: Namespace) -> int:
        try:
            return fn(ctx, args)
        except AppError as exc:
            _print_error(exc.message, exc.hint)
            _write_log(ctx, "ERROR", f"code={exc.exit_code}\n{traceback.format_exc()}")
            return exc.exit_code
        except KeyboardInterrupt:
            _print_error("작업을 중단했습니다.", "")
            return 1
        except Exception:  # noqa: BLE001 - 스택트레이스가 화면에 새지 않게 여기서 막는다
            _print_error(
                "예상치 못한 오류가 발생했습니다.",
                f"자세한 내용은 {ctx.log_path} 를 확인하세요.",
            )
            _write_log(ctx, "ERROR", f"code=1\n{traceback.format_exc()}")
            return 1

    return wrapper


def log_call(fn: Handler) -> Handler:
    """실행한 명령과 인자를 로그에 남긴다. 메모·태그는 내용 대신 길이만 기록한다."""

    @functools.wraps(fn)
    def wrapper(ctx: Context, args: Namespace) -> int:
        command = getattr(args, "command", "?")
        _write_log(ctx, "CALL", f"{command} {_safe_args(args)}")
        try:
            code = fn(ctx, args)
        except BaseException as exc:
            # 예외는 바깥의 handle_errors 가 처리한다. 여기서 EXIT 을 남기지 않으면
            # 로그에 CALL 만 남아 명령이 끝났는지 알 수 없다.
            _write_log(ctx, "EXIT", f"{command} raised={type(exc).__name__}")
            raise
        _write_log(ctx, "EXIT", f"{command} code={code}")
        return code

    return wrapper


def timed(fn: Handler) -> Handler:
    """실행 시간을 잰다. --verbose 일 때만 보여준다."""

    @functools.wraps(fn)
    def wrapper(ctx: Context, args: Namespace) -> int:
        started = time.perf_counter()
        try:
            return fn(ctx, args)
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            if ctx.verbose:
                print(f"[시간] {elapsed:.1f}ms")

    return wrapper


def as_command(fn: Handler) -> Handler:
    """세 데코레이터를 정해진 순서로 적용한다.

    handle_errors 가 가장 바깥이어야 로깅·시간 측정 중에 난 예외까지 잡힌다.
    """
    return handle_errors(log_call(timed(fn)))


def _print_error(message: str, hint: str) -> None:
    print(f"[오류] {message}", file=sys.stderr)
    if hint:
        print(f"[힌트] {hint}", file=sys.stderr)


def _safe_args(args: Namespace) -> str:
    parts = []
    for key, value in sorted(vars(args).items()):
        if key in ("command", "data_dir", "verbose"):
            continue
        if value is None or value is False:
            continue
        if key in _MASKED_FIELDS:
            parts.append(f"{key}=<len:{len(str(value))}>")
        else:
            parts.append(f"{key}={value}")
    return " ".join(parts)


def _write_log(ctx: Context, level: str, text: str) -> None:
    """로그 기록이 명령을 실패시키지 않는다. 로그는 부가 기능이다."""
    try:
        ctx.log_path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().isoformat(timespec="seconds")
        with ctx.log_path.open("a", encoding="utf-8") as fp:
            fp.write(f"{stamp} {level} {text.rstrip()}\n")
    except OSError:
        pass
