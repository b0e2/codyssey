import argparse
from collections.abc import Sequence

from ai_gitgen.ai_client import DEFAULT_MODEL
from ai_gitgen.generator import ConfigurationError, load_convention

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


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_arguments(parser, args)

    try:
        load_convention(args.convention)
    except ConfigurationError as error:
        parser.error(str(error))

    print(f"[INFO] 명령: {args.command}")
    print(f"[INFO] 모델: {args.model}")
    print(f"[INFO] temperature: {args.temperature}")
    print(f"[INFO] max_tokens: {args.max_tokens}")
    print(f"[INFO] safe_mode: {args.safe_mode}")
    print(f"[INFO] convention: {args.convention}")
