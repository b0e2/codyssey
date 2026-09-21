from pathlib import Path
import subprocess

import pytest

from ai_gitgen.cli import main
from ai_gitgen.generator import (
    ConfigurationError,
    load_convention,
    sanitize_diff,
)
from ai_gitgen.git import (
    NotGitRepositoryError,
    NotRepositoryRootError,
    collect_git_context,
)


def _run_git(repository: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    )


def _create_repository(path: Path) -> None:
    _run_git(path, "init", "-b", "main")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "user.email", "test@example.com")
    (path / "sample.txt").write_text("initial\n", encoding="utf-8")
    _run_git(path, "add", "sample.txt")
    _run_git(path, "commit", "-m", "test: initial")


def _diff_block(path: str, content: str) -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        f"{content}"
    )


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


def test_sanitize_diff_masks_sensitive_values() -> None:
    api_key = "gsk_" + "a" * 26
    diff = _diff_block(
        "config.py",
        f"+AI_API_KEY={api_key}\n"
        "+email=user@example.com\n"
        "+DB_PASSWORD=database-password\n"
        "+AWS_SECRET_ACCESS_KEY=cloud-secret",
    )

    result = sanitize_diff(diff)

    assert api_key not in result.text
    assert "user@example.com" not in result.text
    assert "database-password" not in result.text
    assert "cloud-secret" not in result.text
    assert result.masked_value_count == 4


def test_sanitize_diff_excludes_sensitive_files() -> None:
    diff = "\n".join(
        [
            _diff_block(".env", "+AI_API_KEY=value"),
            _diff_block("src/app.py", "+print('ok')"),
        ]
    )

    result = sanitize_diff(diff, exclude_files=[".env", "*.key"])

    assert ".env" not in result.text
    assert "src/app.py" in result.text
    assert result.excluded_file_count == 1


def test_sanitize_diff_limits_files_and_lines() -> None:
    blocks = [
        _diff_block(f"src/file_{index}.py", "+value = 1")
        for index in range(12)
    ]
    long_block = _diff_block(
        "src/large.py",
        "\n".join(f"+line_{index}" for index in range(250)),
    )

    file_limited = sanitize_diff("\n".join(blocks), max_files=10)
    line_limited = sanitize_diff(long_block, max_lines=200)

    assert file_limited.included_file_count == 10
    assert "src/file_10.py" not in file_limited.text
    assert file_limited.truncated is True
    assert line_limited.line_count == 200
    assert line_limited.text.endswith("[diff truncated]")


def test_collect_git_context(tmp_path: Path) -> None:
    _create_repository(tmp_path)
    (tmp_path / "sample.txt").write_text("changed\n", encoding="utf-8")

    context = collect_git_context(tmp_path)

    assert context.branch == "main"
    assert context.changed_files == ("sample.txt",)
    assert context.changed_file_count == 1
    assert context.diff_line_count > 0
    assert context.has_changes is True


def test_collect_git_context_includes_staged_diff(tmp_path: Path) -> None:
    _create_repository(tmp_path)
    (tmp_path / "sample.txt").write_text("staged\n", encoding="utf-8")
    _run_git(tmp_path, "add", "sample.txt")

    context = collect_git_context(tmp_path)

    assert "+staged" in context.diff
    assert context.changed_files == ("sample.txt",)


def test_collect_git_context_requires_repository_root(tmp_path: Path) -> None:
    _create_repository(tmp_path)
    subdirectory = tmp_path / "src"
    subdirectory.mkdir()

    with pytest.raises(NotRepositoryRootError):
        collect_git_context(subdirectory)


def test_collect_git_context_rejects_non_repository(tmp_path: Path) -> None:
    with pytest.raises(NotGitRepositoryError):
        collect_git_context(tmp_path)


def test_cli_exits_when_repository_is_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _create_repository(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["commit"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "변경 사항이 없습니다" in output
