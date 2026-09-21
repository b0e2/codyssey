from pathlib import Path

import pytest

from ai_gitgen.generator import ConfigurationError, load_convention


def test_load_convention(tmp_path: Path) -> None:
    config_path = tmp_path / "convention.yml"
    config_path.write_text("commit:\n  title_max_length: 72\n", encoding="utf-8")

    config = load_convention(config_path)

    assert config["commit"]["title_max_length"] == 72


def test_load_convention_rejects_non_mapping(tmp_path: Path) -> None:
    config_path = tmp_path / "convention.yml"
    config_path.write_text("- invalid\n", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_convention(config_path)
