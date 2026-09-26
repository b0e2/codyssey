from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pytest
import requests

import git_gen.cli as cli_module
from git_gen.llm_client import (
    APIRequestError,
    AuthenticationError,
    LLMClient,
    InvalidResponseError,
    MissingAPIEndpointError,
    NetworkError,
    RateLimitError,
)
from git_gen.cli import main
from git_gen.generator import (
    ConfigurationError,
    OutputFormatError,
    build_messages,
    format_commit_output,
    format_pr_output,
    load_convention,
    response_schema_for,
    sanitize_diff,
    validate_output_config,
)
from git_gen.git import (
    GitContext,
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
    generic_key = "sk-proj-" + "b" * 26
    diff = _diff_block(
        "config.py",
        f"+LLM_API_KEY={api_key}\n"
        f"+value = '{generic_key}'\n"
        "+email=user@example.com\n"
        "+DB_PASSWORD=database-password\n"
        "+AWS_SECRET_ACCESS_KEY=cloud-secret",
    )

    result = sanitize_diff(diff)

    assert api_key not in result.text
    assert generic_key not in result.text
    assert "user@example.com" not in result.text
    assert "database-password" not in result.text
    assert "cloud-secret" not in result.text
    assert result.masked_value_count == 5


def test_sanitize_diff_excludes_sensitive_files() -> None:
    diff = "\n".join(
        [
            _diff_block(".env", "+LLM_API_KEY=value"),
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


class _FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: Any = None,
        *,
        json_error: bool = False,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self) -> Any:
        if self._json_error:
            raise ValueError("invalid json")
        return self._payload


class _FakeSession:
    def __init__(
        self,
        response: _FakeResponse | None = None,
        error: requests.RequestException | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append({"url": url, **kwargs})
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response


def test_llm_client_sends_strict_schema_request() -> None:
    content = json.dumps(
        {"title": "feat: 변경 사항 요약", "body": []},
        ensure_ascii=False,
    )
    session = _FakeSession(
        _FakeResponse(
            200,
            {"choices": [{"message": {"content": content}}]},
        )
    )
    client = LLMClient(
        "test-key",
        "https://llm.example/v1/chat/completions",
        session=session,
    )
    schema_name, schema = response_schema_for("commit")

    result = client.generate(
        messages=[{"role": "user", "content": "test"}],
        schema_name=schema_name,
        schema=schema,
        model="openai/gpt-oss-20b",
        temperature=0.2,
        max_tokens=800,
    )

    assert result["title"] == "feat: 변경 사항 요약"
    assert client.request_count == 1
    assert len(session.calls) == 1
    assert session.calls[0]["url"] == "https://llm.example/v1/chat/completions"
    assert session.calls[0]["headers"]["Authorization"] == "Bearer test-key"
    request_json = session.calls[0]["json"]
    assert request_json["max_completion_tokens"] == 800
    assert "max_tokens" not in request_json
    assert request_json["response_format"]["json_schema"]["strict"] is True


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [(401, AuthenticationError), (403, AuthenticationError), (429, RateLimitError)],
)
def test_llm_client_classifies_http_errors(
    status_code: int,
    error_type: type[Exception],
) -> None:
    session = _FakeSession(_FakeResponse(status_code, {"error": {}}))
    client = LLMClient(
        "test-key",
        "https://llm.example/v1/chat/completions",
        session=session,
    )

    with pytest.raises(error_type):
        client.generate(
            messages=[],
            schema_name="test",
            schema={"type": "object"},
            model="test-model",
            temperature=0.2,
            max_tokens=100,
        )


def test_llm_client_reports_generic_http_error() -> None:
    session = _FakeSession(
        _FakeResponse(500, {"error": {"message": "server error"}})
    )
    client = LLMClient(
        "test-key",
        "https://llm.example/v1/chat/completions",
        session=session,
    )

    with pytest.raises(APIRequestError, match="HTTP 500.*server error"):
        client.generate(
            messages=[],
            schema_name="test",
            schema={"type": "object"},
            model="test-model",
            temperature=0.2,
            max_tokens=100,
        )


def test_llm_client_classifies_network_error() -> None:
    session = _FakeSession(error=requests.ConnectionError("offline"))
    client = LLMClient(
        "test-key",
        "https://llm.example/v1/chat/completions",
        session=session,
    )

    with pytest.raises(NetworkError):
        client.generate(
            messages=[],
            schema_name="test",
            schema={"type": "object"},
            model="test-model",
            temperature=0.2,
            max_tokens=100,
        )


def test_llm_client_rejects_invalid_json() -> None:
    session = _FakeSession(
        _FakeResponse(
            200,
            {"choices": [{"message": {"content": "not-json"}}]},
        )
    )
    client = LLMClient(
        "test-key",
        "https://llm.example/v1/chat/completions",
        session=session,
    )

    with pytest.raises(InvalidResponseError):
        client.generate(
            messages=[],
            schema_name="test",
            schema={"type": "object"},
            model="test-model",
            temperature=0.2,
            max_tokens=100,
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"choices": []},
        {"choices": [{"message": {"content": "[]"}}]},
    ],
)
def test_llm_client_rejects_invalid_response_shape(payload: dict[str, Any]) -> None:
    session = _FakeSession(_FakeResponse(200, payload))
    client = LLMClient(
        "test-key",
        "https://llm.example/v1/chat/completions",
        session=session,
    )

    with pytest.raises(InvalidResponseError):
        client.generate(
            messages=[],
            schema_name="test",
            schema={"type": "object"},
            model="test-model",
            temperature=0.2,
            max_tokens=100,
        )


def test_build_messages_and_output_formatting() -> None:
    messages = build_messages(
        command="commit",
        branch="feature/test",
        status=" M sample.py",
        diff="+print('changed')",
        config={"commit": {"prefixes": ["feat", "fix"]}},
    )
    config = {
        "commit": {"prefixes": ["feat", "fix"]},
        "pull_request": {},
    }
    commit_output = format_commit_output(
        {"title": "feat: 출력 추가", "body": ["터미널 출력 추가"]},
        config,
    )
    pr_output = format_pr_output(
        {
            "title": "feat: 출력 추가",
            "why": ["초안 생성 필요"],
            "what": ["출력 기능 추가"],
            "how_to_test": ["명령 실행"],
        },
        config,
    )

    assert "feature/test" in messages[1]["content"]
    assert "+print('changed')" in messages[1]["content"]
    assert "모든 자연어는 반드시 한국어" in messages[0]["content"]
    assert "--- Commit Message ---" in commit_output
    assert "## Why" in pr_output
    assert "## What" in pr_output
    assert "## How to Test" in pr_output


def test_output_config_rejects_too_short_commit_title_limit() -> None:
    with pytest.raises(ConfigurationError, match="너무 짧습니다"):
        validate_output_config(
            "commit",
            {"commit": {"title_max_length": 6, "prefixes": ["feat"]}},
        )


def test_commit_output_normalizes_and_truncates() -> None:
    output = format_commit_output(
        {
            "title": f"feat: {'가' * 100}\n두 번째 줄",
            "body": [
                "- 첫 번째 변경",
                "* 두 번째 변경",
                "3. 세 번째 변경",
                "네 번째 변경",
            ],
        },
        {"commit": {"title_max_length": 72, "prefixes": ["feat"]}},
    )
    lines = output.splitlines()

    assert len(lines[1]) == 72
    assert lines[1].endswith("…")
    assert "- 첫 번째 변경" in lines
    assert "- 두 번째 변경" in lines
    assert "- 세 번째 변경" in lines
    assert "네 번째 변경" not in output


def test_commit_output_replaces_english_title_with_korean_body() -> None:
    output = format_commit_output(
        {
            "title": "feat: validate generated output",
            "body": ["생성 결과 형식 검증 추가"],
        },
        {"commit": {"prefixes": ["feat"]}},
    )

    assert "feat: 생성 결과 형식 검증 추가" in output


def test_commit_output_revalidates_korean_after_truncation() -> None:
    output = format_commit_output(
        {
            "title": f"feat: {'english ' * 20}한글",
            "body": ["한국어 대체 제목"],
        },
        {"commit": {"prefixes": ["feat"], "title_max_length": 30}},
    )

    assert output.splitlines()[1] == "feat: 한국어 대체 제목"


def test_commit_output_rejects_unconfigured_prefix() -> None:
    with pytest.raises(OutputFormatError, match="prefix"):
        format_commit_output(
            {"title": "docs: 문서 수정", "body": []},
            {"commit": {"prefixes": ["feat", "fix"]}},
        )


def test_pr_output_applies_title_limit_and_custom_sections() -> None:
    output = format_pr_output(
        {
            "title": "긴 PR 제목을 설정 길이에 맞게 줄이는 변경 사항",
            "why": ["- 변경 이유"],
            "what": ["* 변경 내용\n- 추가 항목"],
            "how_to_test": ["1. pytest 실행\n2. CLI 실행"],
        },
        {
            "pull_request": {
                "title_max_length": 20,
                "sections": ["배경", "변경 사항", "테스트"],
            }
        },
    )
    lines = output.splitlines()

    assert len(lines[1]) <= 20
    assert lines[1].endswith("…")
    assert "## 배경" in output
    assert "## 변경 사항" in output
    assert "## 테스트" in output
    assert "- 변경 이유" in output
    assert "- 변경 내용" in output
    assert "- 추가 항목" in output
    assert "- pytest 실행" in output
    assert "- CLI 실행" in output


def test_pr_output_replaces_english_title_with_korean_change() -> None:
    output = format_pr_output(
        {
            "title": "add output validation",
            "why": ["안정적인 출력 필요"],
            "what": ["생성 결과 검증 추가"],
            "how_to_test": ["pytest 실행"],
        },
        {"pull_request": {}},
    )

    assert output.splitlines()[1] == "생성 결과 검증 추가"


def test_pr_output_revalidates_korean_after_truncation() -> None:
    output = format_pr_output(
        {
            "title": f"{'english ' * 20}한글",
            "why": ["technical reason"],
            "what": ["technical change"],
            "how_to_test": ["한국어 테스트"],
        },
        {"pull_request": {"title_max_length": 30}},
    )

    assert output.splitlines()[1] == "한국어 테스트"


def test_pr_output_rejects_missing_required_items() -> None:
    with pytest.raises(OutputFormatError, match="why"):
        format_pr_output(
            {
                "title": "PR 제목",
                "why": [],
                "what": ["변경 내용"],
                "how_to_test": ["pytest 실행"],
            },
            {"pull_request": {}},
        )


class _StubClient:
    last_instance: "_StubClient | None" = None

    def __init__(self, api_key: str, endpoint: str) -> None:
        assert api_key == "test-key"
        assert endpoint == "https://llm.example/v1/chat/completions"
        self.request_count = 0
        self.kwargs: dict[str, Any] = {}
        _StubClient.last_instance = self

    def generate(self, **kwargs: Any) -> dict[str, Any]:
        self.request_count += 1
        self.kwargs = kwargs
        if kwargs["schema_name"] == "commit_message":
            return {"title": "feat: CLI 출력 추가", "body": ["요청 결과 출력"]}
        return {
            "title": "feat: CLI 출력 추가",
            "why": ["초안 생성 필요"],
            "what": ["CLI 출력 추가"],
            "how_to_test": ["명령 실행"],
        }


@pytest.mark.parametrize(
    ("command", "expected"),
    [("commit", "--- Commit Message ---"), ("pr", "--- PR Body ---")],
)
def test_cli_calls_api_once_and_prints_result(
    command: str,
    expected: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context = GitContext(
        root=tmp_path,
        branch="feature/test",
        status=" M sample.py",
        diff=_diff_block("sample.py", "+changed = True"),
        changed_files=("sample.py",),
    )
    monkeypatch.setattr(cli_module, "collect_git_context", lambda: context)
    loaded_paths: list[str] = []

    def fake_load_convention(path: str) -> dict[str, Any]:
        loaded_paths.append(path)
        return {
            "commit": {},
            "pull_request": {},
            "safe_mode": {"max_files": 10, "max_lines": 200},
        }

    monkeypatch.setattr(cli_module, "load_convention", fake_load_convention)
    monkeypatch.setattr(cli_module, "LLMClient", _StubClient)
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv(
        "LLM_API_ENDPOINT",
        "https://llm.example/v1/chat/completions",
    )

    exit_code = main(
        [
            command,
            "--temperature",
            "0.4",
            "--max-tokens",
            "321",
            "--convention",
            "custom.yml",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert expected in output
    assert "API 호출 횟수: 1" in output
    assert _StubClient.last_instance is not None
    assert _StubClient.last_instance.request_count == 1
    assert _StubClient.last_instance.kwargs["temperature"] == 0.4
    assert _StubClient.last_instance.kwargs["max_tokens"] == 321
    assert loaded_paths == ["custom.yml"]


def test_cli_reports_missing_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context = GitContext(
        root=tmp_path,
        branch="feature/test",
        status=" M sample.py",
        diff=_diff_block("sample.py", "+changed = True"),
        changed_files=("sample.py",),
    )
    monkeypatch.setattr(cli_module, "collect_git_context", lambda: context)
    monkeypatch.setattr(
        cli_module,
        "load_convention",
        lambda _: {
            "commit": {},
            "safe_mode": {"max_files": 10, "max_lines": 200},
        },
    )
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv(
        "LLM_API_ENDPOINT",
        "https://llm.example/v1/chat/completions",
    )

    exit_code = main(["commit"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "LLM_API_KEY 환경변수가 설정되지 않았습니다" in output


def test_llm_client_reports_missing_endpoint() -> None:
    with pytest.raises(MissingAPIEndpointError, match="LLM_API_ENDPOINT"):
        LLMClient("test-key", "")
