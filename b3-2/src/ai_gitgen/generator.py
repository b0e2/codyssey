"""Prompt generation, safe mode, and output validation."""

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
import re
from typing import Any

import yaml


class ConfigurationError(Exception):
    """Raised when the convention file is missing or invalid."""


@dataclass(frozen=True)
class SafeDiffResult:
    """Result of masking and limiting a diff."""

    text: str
    original_file_count: int
    included_file_count: int
    excluded_file_count: int
    line_count: int
    masked_value_count: int
    truncated: bool


_GROQ_KEY_PATTERN = re.compile(r"\bgsk_[A-Za-z0-9_-]+\b")
_BEARER_PATTERN = re.compile(
    r"(?i)(authorization\s*:\s*bearer\s+)[^\s\"']+"
)
_SECRET_PATTERN = re.compile(
    r"(?i)(\b[A-Za-z0-9_-]*"
    r"(?:api[_-]?key|access[_-]?token|secret|password)"
    r"[A-Za-z0-9_-]*\b\s*[:=]\s*)"
    r"([\"']?)([^\"'\s,]+)([\"']?)"
)
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
_DIFF_HEADER_PATTERN = re.compile(r"(?m)^diff --git .+$")


def load_convention(path: str | Path) -> dict[str, Any]:
    """Load a YAML convention file and validate its root structure."""
    config_path = Path(path)

    if not config_path.is_file():
        raise ConfigurationError(
            f"컨벤션 설정 파일을 찾을 수 없습니다: {config_path}"
        )

    try:
        with config_path.open(encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as error:
        raise ConfigurationError(
            f"컨벤션 설정 파일 형식이 올바르지 않습니다: {config_path}"
        ) from error

    if not isinstance(config, dict):
        raise ConfigurationError(
            f"컨벤션 설정의 최상위 값은 객체여야 합니다: {config_path}"
        )

    return config


def _split_diff_blocks(diff: str) -> list[str]:
    matches = list(_DIFF_HEADER_PATTERN.finditer(diff))

    if not matches:
        return [diff.rstrip()] if diff.strip() else []

    blocks: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(diff)
        blocks.append(diff[match.start():end].rstrip())

    return blocks


def _extract_diff_path(block: str) -> str:
    new_path = re.search(r"(?m)^\+\+\+ b/(.+)$", block)
    if new_path:
        return new_path.group(1).strip().strip('"')

    old_path = re.search(r"(?m)^--- a/(.+)$", block)
    if old_path:
        return old_path.group(1).strip().strip('"')

    return ""


def _matches_exclude_pattern(path: str, patterns: list[str]) -> bool:
    file_name = Path(path).name
    return any(
        fnmatch(path, pattern) or fnmatch(file_name, pattern)
        for pattern in patterns
    )


def _mask_sensitive_values(text: str, mask_email: bool) -> tuple[str, int]:
    masked_count = 0

    def replace_secret(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}[MASKED_SECRET]{match.group(4)}"

    text, count = _SECRET_PATTERN.subn(replace_secret, text)
    masked_count += count

    text, count = _GROQ_KEY_PATTERN.subn("[MASKED_API_KEY]", text)
    masked_count += count

    text, count = _BEARER_PATTERN.subn(
        r"\1[MASKED_TOKEN]",
        text,
    )
    masked_count += count

    if mask_email:
        text, count = _EMAIL_PATTERN.subn("[MASKED_EMAIL]", text)
        masked_count += count

    return text, masked_count


def sanitize_diff(
    diff: str,
    *,
    max_files: int = 10,
    max_lines: int = 200,
    exclude_files: list[str] | None = None,
    mask_email: bool = True,
) -> SafeDiffResult:
    """Mask sensitive values and limit diff size before an API request."""
    if max_files < 1:
        raise ValueError("max_files는 1 이상이어야 합니다.")
    if max_lines < 1:
        raise ValueError("max_lines는 1 이상이어야 합니다.")

    blocks = _split_diff_blocks(diff)
    patterns = exclude_files or []
    allowed_blocks: list[str] = []
    excluded_file_count = 0

    for block in blocks:
        path = _extract_diff_path(block)
        if path and _matches_exclude_pattern(path, patterns):
            excluded_file_count += 1
            continue
        allowed_blocks.append(block)

    selected_blocks = allowed_blocks[:max_files]
    truncated = len(allowed_blocks) > max_files
    combined = "\n".join(selected_blocks)
    masked, masked_value_count = _mask_sensitive_values(
        combined,
        mask_email,
    )

    lines = masked.splitlines()
    if len(lines) > max_lines:
        truncated = True
        if max_lines == 1:
            lines = ["[diff truncated]"]
        else:
            lines = lines[: max_lines - 1] + ["[diff truncated]"]

    text = "\n".join(lines)

    return SafeDiffResult(
        text=text,
        original_file_count=len(blocks),
        included_file_count=len(selected_blocks),
        excluded_file_count=excluded_file_count,
        line_count=len(lines),
        masked_value_count=masked_value_count,
        truncated=truncated,
    )
