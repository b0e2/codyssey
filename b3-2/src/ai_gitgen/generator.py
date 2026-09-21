"""Prompt generation, safe mode, and output validation."""

from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(Exception):
    """Raised when the convention file is missing or invalid."""


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
