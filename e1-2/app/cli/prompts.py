"""사용자 입력 처리 및 검증 함수"""

class ExitRequested(Exception):
    """KeyboardInterrupt (Ctrl + C), EOF Event"""


def read_int(label: str, min_value: int, max_value: int) -> int:
    while True:
        text = _read_raw(label).strip()
        if not text:
            print("⚠️  빈 입력입니다. 다시 입력해 주세요.")
            continue
        try:
            value = int(text)
        except ValueError:
            print("⚠️ 숫자로 입력해 주세요.")
            continue
        if not (min_value <= value <= max_value):
            print(f"⚠️ {min_value}에서 {max_value} 사이의 숫자를 입력해 주세요.")
            continue
        return value


def read_text(label: str) -> str:
    while True:
        text = _read_raw(label).strip()
        if not text:
            print("⚠️  빈 입력입니다. 다시 입력해 주세요.")
            continue
        return text


def read_text_optional(label: str) -> str:
    return _read_raw(label).strip()


def read_int_optional(label: str, min_value: int, max_value: int) -> int | None:
    """빈 입력이면 None을 반환한다. 수정 화면에서 '기존 값 유지'에 쓴다."""
    while True:
        text = _read_raw(label).strip()
        if not text:
            return None
        try:
            value = int(text)
        except ValueError:
            print("⚠️ 숫자로 입력해 주세요.")
            continue
        if not (min_value <= value <= max_value):
            print(f"⚠️ {min_value}에서 {max_value} 사이의 숫자를 입력해 주세요.")
            continue
        return value


def read_yes_no(label: str) -> bool:
    """y/n 입력을 받아 참/거짓으로 돌려준다."""
    while True:
        text = _read_raw(label).strip().lower()
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        print("⚠️ y 또는 n으로 입력해 주세요.")


def _read_raw(label: str) -> str:
    try:
        return input(label)
    except (KeyboardInterrupt, EOFError):
        print()
        raise ExitRequested from None