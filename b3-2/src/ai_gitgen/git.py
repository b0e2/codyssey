"""Git repository validation and change collection."""

from dataclasses import dataclass
from pathlib import Path
import subprocess


class GitError(Exception):
    """Base exception for Git failures."""


class GitCommandError(GitError):
    """Raised when a Git command fails."""


class NotGitRepositoryError(GitError):
    """Raised when the current directory is not a Git repository."""


class NotRepositoryRootError(GitError):
    """Raised when the command is not executed from the repository root."""


@dataclass(frozen=True)
class GitContext:
    """Git information used to build a generation request."""

    root: Path
    branch: str
    status: str
    diff: str
    changed_files: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        return bool(self.status.strip() or self.diff.strip())

    @property
    def changed_file_count(self) -> int:
        return len(self.changed_files)

    @property
    def diff_line_count(self) -> int:
        return len(self.diff.splitlines())


def _run_git(*args: str, cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise GitError("Git 실행 파일을 찾을 수 없습니다.") from error
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or "Git 명령 실행 실패"
        raise GitCommandError(message) from error

    return result.stdout.rstrip()


def get_repository_root(cwd: Path) -> Path:
    try:
        root = _run_git("rev-parse", "--show-toplevel", cwd=cwd)
    except GitCommandError as error:
        raise NotGitRepositoryError(
            "현재 위치는 Git 저장소가 아닙니다."
        ) from error

    return Path(root).resolve()


def parse_changed_files(status: str) -> tuple[str, ...]:
    files: list[str] = []

    for line in status.splitlines():
        if len(line) < 4:
            continue

        path = line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", maxsplit=1)[-1]
        files.append(path.strip('"'))

    return tuple(files)


def collect_git_context(cwd: str | Path | None = None) -> GitContext:
    current_directory = Path(cwd or Path.cwd()).resolve()
    root = get_repository_root(current_directory)

    if current_directory != root:
        raise NotRepositoryRootError(
            f"프로젝트 루트에서 실행해 주세요: {root}"
        )

    branch = _run_git("branch", "--show-current", cwd=root) or "(detached HEAD)"
    status = _run_git(
        "status",
        "--short",
        "--untracked-files=all",
        cwd=root,
    )
    unstaged_diff = _run_git(
        "diff",
        "--no-ext-diff",
        "--no-color",
        cwd=root,
    )
    staged_diff = _run_git(
        "diff",
        "--cached",
        "--no-ext-diff",
        "--no-color",
        cwd=root,
    )
    diff = "\n".join(
        part for part in (staged_diff, unstaged_diff) if part
    )

    return GitContext(
        root=root,
        branch=branch,
        status=status,
        diff=diff,
        changed_files=parse_changed_files(status),
    )
