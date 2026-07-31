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


def _read_raw(label: str) -> str:
    try:
        return input(label)
    except (KeyboardInterrupt, EOFError):
        print()
        raise ExitRequested from None