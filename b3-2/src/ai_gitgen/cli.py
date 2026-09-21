import argparse
from collections.abc import Sequence
from typing import Any

from ai_gitgen.ai_client import DEFAULT_MODEL
from ai_gitgen.generator import (
    ConfigurationError,
    load_convention,
    sanitize_diff,
)
from ai_gitgen.git import GitError, collect_git_context

DEFAULT_TEMPERATURE = 0.2
COMMIT_DEFAULT_MAX_TOKENS = 800
PR_DEFAULT_MAX_TOKENS = 1500


def add_generation_options(
    parser: argparse.ArgumentParser,
    default_max_tokens: int,
) -> None:
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"사용할 Groq 모델, 기본값: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"생성 다양성, 기본값: {DEFAULT_TEMPERATURE}",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=default_max_tokens,
        help=f"최대 생성 토큰 수, 기본값: {default_max_tokens}",
    )
    parser.add_argument(
        "--safe-mode",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="민감정보 마스킹과 diff 전송 제한 적용",
    )
    parser.add_argument(
        "--convention",
        default=".ai-gitgen.yml",
        help="컨벤션 설정 파일 경로",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-gitgen",
        description="Git 변경 사항을 기반으로 커밋 메시지와 PR 초안을 생성합니다.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit_parser = subparsers.add_parser(
        "commit",
        help="커밋 메시지를 생성합니다.",
    )
    add_generation_options(commit_parser, COMMIT_DEFAULT_MAX_TOKENS)

    pr_parser = subparsers.add_parser(
        "pr",
        help="PR 제목과 본문을 생성합니다.",
    )
    add_generation_options(pr_parser, PR_DEFAULT_MAX_TOKENS)

    return parser


def validate_arguments(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if not 0 <= args.temperature <= 2:
        parser.error("--temperature는 0 이상 2 이하로 입력해야 합니다.")

    if args.max_tokens <= 0:
        parser.error("--max-tokens는 1 이상의 정수여야 합니다.")


def _safe_mode_options(config: dict[str, Any]) -> dict[str, Any]:
    safe_mode = config.get("safe_mode", {})
    if not isinstance(safe_mode, dict):
        raise ConfigurationError("safe_mode 설정은 객체여야 합니다.")

    exclude_files = safe_mode.get("exclude_files", [])
    if not isinstance(exclude_files, list) or not all(
        isinstance(item, str) for item in exclude_files
    ):
        raise ConfigurationError("safe_mode.exclude_files는 문자열 목록이어야 합니다.")

    return {
        "max_files": int(safe_mode.get("max_files", 10)),
        "max_lines": int(safe_mode.get("max_lines", 200)),
        "mask_email": bool(safe_mode.get("mask_email", True)),
        "exclude_files": exclude_files,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_arguments(parser, args)

    try:
        context = collect_git_context()
    except GitError as error:
        print(f"[ERROR] {error}")
        return 1

    print(f"[INFO] 현재 브랜치: {context.branch}")
    print(
        f"[INFO] Git status 수집 완료: "
        f"{context.changed_file_count}개 파일 변경 감지"
    )

    if not context.has_changes:
        print("[INFO] 변경 사항이 없습니다. 생성을 종료합니다.")
        return 0

    print(f"[INFO] Git diff 수집 완료: {context.diff_line_count}줄")

    try:
        config = load_convention(args.convention)
        if args.safe_mode:
            safe_diff = sanitize_diff(
                context.diff,
                **_safe_mode_options(config),
            )
            print(
                f"[INFO] safe mode 적용 완료: "
                f"{safe_diff.included_file_count}개 파일, "
                f"{safe_diff.line_count}줄, "
                f"{safe_diff.masked_value_count}건 마스킹"
            )
        else:
            print("[WARN] safe mode가 비활성화되었습니다.")
    except (ConfigurationError, TypeError, ValueError) as error:
        print(f"[ERROR] {error}")
        return 1

    print(f"[INFO] 명령: {args.command}")
    print(f"[INFO] 모델: {args.model}")
    print(f"[INFO] temperature: {args.temperature}")
    print(f"[INFO] max_tokens: {args.max_tokens}")
    return 0
