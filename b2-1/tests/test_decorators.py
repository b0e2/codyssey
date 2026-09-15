"""공통 관심사 데코레이터 테스트."""

from __future__ import annotations

import io
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from budget_app.decorators import as_command, handle_errors, log_call, timed
from budget_app.models import Context, NotFoundError, ValidationError


class DecoratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def ctx(self, verbose: bool = False) -> Context:
        return Context(data_dir=self.root, verbose=verbose)

    @staticmethod
    def args(**over: object) -> Namespace:
        base = {"command": "list", "data_dir": Path("."), "verbose": False}
        base.update(over)
        return Namespace(**base)

    def run_handler(self, handler, ctx=None, args=None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = handler(ctx or self.ctx(), args or self.args())
        return code, out.getvalue(), err.getvalue()

    def log_text(self) -> str:
        path = self.root / "app.log"
        return path.read_text(encoding="utf-8") if path.exists() else ""


class HandleErrorsTest(DecoratorTestCase):
    def test_passes_through_return_code(self) -> None:
        code, _, err = self.run_handler(handle_errors(lambda ctx, args: 0))
        self.assertEqual(code, 0)
        self.assertEqual(err, "")

    def test_app_error_uses_its_exit_code(self) -> None:
        def handler(ctx, args):
            raise NotFoundError("거래를 찾을 수 없습니다.", "id 를 확인하세요.")

        code, _, err = self.run_handler(handle_errors(handler))
        self.assertEqual(code, 3)
        self.assertIn("[오류] 거래를 찾을 수 없습니다.", err)
        self.assertIn("[힌트] id 를 확인하세요.", err)

    def test_validation_error_is_exit_two(self) -> None:
        def handler(ctx, args):
            raise ValidationError("금액은 0보다 커야 합니다.")

        code, _, _ = self.run_handler(handle_errors(handler))
        self.assertEqual(code, 2)

    def test_unexpected_error_is_exit_one(self) -> None:
        def handler(ctx, args):
            raise RuntimeError("boom")

        code, _, err = self.run_handler(handle_errors(handler))
        self.assertEqual(code, 1)
        self.assertIn("예상치 못한 오류", err)

    def test_traceback_never_reaches_the_screen(self) -> None:
        def handler(ctx, args):
            raise RuntimeError("boom")

        _, out, err = self.run_handler(handle_errors(handler))
        for stream in (out, err):
            self.assertNotIn("Traceback", stream)
            self.assertNotIn("RuntimeError", stream)
        # 대신 로그에는 남아 있어야 조사할 수 있다.
        self.assertIn("Traceback", self.log_text())

    def test_logging_failure_does_not_break_command(self) -> None:
        # data_dir 가 파일이면 로그 디렉터리를 만들 수 없다. 로그는 부가 기능이므로
        # 명령 자체는 정상 종료해야 한다.
        blocker = self.root / "blocker"
        blocker.write_text("", encoding="utf-8")
        ctx = Context(data_dir=blocker, verbose=False)
        code, _, _ = self.run_handler(as_command(lambda c, a: 0), ctx=ctx)
        self.assertEqual(code, 0)


class LogCallTest(DecoratorTestCase):
    def test_records_call_and_exit(self) -> None:
        self.run_handler(log_call(lambda ctx, args: 0))
        text = self.log_text()
        self.assertIn("CALL list", text)
        self.assertIn("EXIT list code=0", text)

    def test_masks_memo_and_tags(self) -> None:
        args = self.args(memo="점심 약속", tags="meal,lunch", amount=15000)
        self.run_handler(log_call(lambda ctx, a: 0), args=args)
        text = self.log_text()
        self.assertIn("memo=<len:5>", text)
        self.assertIn("tags=<len:10>", text)
        self.assertNotIn("점심 약속", text)
        self.assertIn("amount=15000", text)  # 민감하지 않은 값은 그대로 남긴다


class TimedTest(DecoratorTestCase):
    def test_quiet_by_default(self) -> None:
        _, out, _ = self.run_handler(timed(lambda ctx, args: 0))
        self.assertNotIn("[시간]", out)

    def test_prints_when_verbose(self) -> None:
        _, out, _ = self.run_handler(timed(lambda ctx, args: 0), ctx=self.ctx(verbose=True))
        self.assertIn("[시간]", out)

    def test_measures_even_on_failure(self) -> None:
        def handler(ctx, args):
            raise ValidationError("bad")

        _, out, _ = self.run_handler(as_command(handler), ctx=self.ctx(verbose=True))
        self.assertIn("[시간]", out)


class OrderTest(DecoratorTestCase):
    def test_handle_errors_is_outermost(self) -> None:
        # 로깅·시간 측정 중에 난 예외까지 잡혀야 한다.
        def handler(ctx, args):
            raise ValidationError("bad", "고치세요.")

        code, _, err = self.run_handler(as_command(handler))
        self.assertEqual(code, 2)
        self.assertIn("[힌트] 고치세요.", err)

    def test_log_pairs_call_with_exit_even_on_failure(self) -> None:
        def handler(ctx, args):
            raise ValidationError("bad")

        self.run_handler(as_command(handler))
        text = self.log_text()
        self.assertIn("CALL list", text)
        self.assertIn("EXIT list raised=ValidationError", text)
        self.assertIn("ERROR code=2", text)


if __name__ == "__main__":
    unittest.main()
