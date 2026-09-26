"""계층 규칙 테스트.

폴더는 경계를 강제하지 못한다. `service/` 안에서 `cli` 를 import 해도
파이썬은 아무 말도 하지 않는다. 그래서 의존 방향을 여기서 검사한다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

PACKAGE = "budget_app"
ROOT = Path(__file__).resolve().parent.parent / PACKAGE

# 모듈 -> import 해도 되는 내부 모듈
ALLOWED: dict[str, set[str]] = {
    # 의존은 아래로만 흐른다: cli → service → storage → models → validators → errors
    "errors": set(),
    "validators": {"errors"},
    "models": {"errors", "validators"},
    # 저장소는 도메인 타입을 모른다. 예외만 공유한다.
    "storage": {"errors"},
    "decorators": {"errors", "models"},
    "cli.parser": set(),
    "cli.prompts": {"errors", "cli.render"},
    "cli.render": {"models"},
    "service.reading": {"errors", "models", "storage"},
    "service.ledger": {"errors", "models", "validators", "storage", "service.reading"},
    "service.categories": {"errors", "models", "validators", "service.ledger"},
    "service.reports": {
        "errors", "models", "validators", "storage", "service.ledger", "service.reading"
    },
    "service.porting": {
        "errors", "models", "validators", "storage", "service.ledger", "service.reading"
    },
    "service.recurring": {
        "errors", "models", "validators", "storage", "service.ledger", "service.reading"
    },
    "cli.app": {
        "errors",
        "models",
        "validators",
        "decorators",
        "cli.parser",
        "cli.prompts",
        "cli.render",
        "service.ledger",
        "service.categories",
        "service.reports",
        "service.porting",
        "service.recurring",
    },
    # 조립 지점. 서비스나 저장소를 직접 부르지 않는다.
    "__main__": {"cli.app"},
}


def module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    return ".".join(rel.parts)


def internal_imports(path: Path) -> list[tuple[str, list[str]]]:
    """(대상 모듈, 가져온 이름들) 목록."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[str, list[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(PACKAGE):
            target = (node.module or "")[len(PACKAGE) + 1 :]
            found.append((target, [alias.name for alias in node.names]))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PACKAGE):
                    found.append((alias.name[len(PACKAGE) + 1 :], []))
    return found


def source_modules() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.py") if p.name != "__init__.py")


class LayerTest(unittest.TestCase):
    def test_every_module_is_covered_by_the_rule_table(self) -> None:
        names = {module_name(p) for p in source_modules()}
        self.assertEqual(names, set(ALLOWED), "새 모듈은 계층 규칙 표에도 넣어야 한다")

    def test_dependencies_point_downward(self) -> None:
        for path in source_modules():
            name = module_name(path)
            for target, _ in internal_imports(path):
                with self.subTest(module=name, imports=target):
                    self.assertIn(
                        target,
                        ALLOWED[name],
                        f"{name} 은 {target} 을 import 할 수 없다",
                    )

    def test_errors_sit_at_the_bottom(self) -> None:
        self.assertEqual(internal_imports(ROOT / "errors.py"), [])

    def test_storage_knows_no_domain_type(self) -> None:
        # 저장소는 dict 만 흘린다. Transaction 이나 Query 를 알면 계층이 샌다.
        # 예외를 별도 모듈로 둔 덕분에 이름을 하나하나 보지 않아도 규칙으로 드러난다.
        for target, _ in internal_imports(ROOT / "storage.py"):
            self.assertEqual(target, "errors")

    def test_cli_does_not_reach_storage_directly(self) -> None:
        for path in (ROOT / "cli").glob("*.py"):
            for target, _ in internal_imports(path):
                self.assertNotEqual(target, "storage")


if __name__ == "__main__":
    unittest.main()
