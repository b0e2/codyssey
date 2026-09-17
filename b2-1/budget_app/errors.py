"""오류 계층.

의존 그래프의 맨 아래다. 종료 코드를 예외 자신이 들고 다니므로, 명령을
감싸는 데코레이터는 무엇이 잘못됐는지 따지지 않고 `exit_code` 만 돌려주면 된다.
"""

from __future__ import annotations

class AppError(Exception):
    """사용자에게 원인과 해결 힌트를 보여줄 수 있는 오류.

    스택트레이스 대신 message + hint 를 출력하고 exit_code 로 종료하기 위해
    종료 코드를 예외 자신이 들고 다닌다.
    """

    exit_code = 1

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(AppError):
    """입력 형식·값이 규칙에 맞지 않음."""

    exit_code = 2


class NotFoundError(AppError):
    """존재해야 할 자원을 찾지 못함 (거래 id, 카테고리, 규칙)."""

    exit_code = 3


class StorageError(AppError):
    """파일 I/O 실패 또는 저장 데이터 손상."""

    exit_code = 4


