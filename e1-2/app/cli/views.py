"""화면에 출력할 문자열을 생성한다. print는 하지 않는다."""


def title(categories: tuple[str, ...], labels: dict[str, str]) -> str:
    lines = ["=" * 40, "        🐍 파이썬 퀴즈 게임 🐍", "=" * 40]
    lines += [f"  - {labels[category]}" for category in categories]
    lines.append("=" * 40)
    return "\n".join(lines)


def menu(items: dict[int, str]) -> str:
    lines = [f"{number}. {label}" for number, label in items.items()]
    return "\n".join(lines)


def data_created(quiz_count: int) -> str:
    return f"📂 저장된 데이터가 없어 기본 퀴즈 {quiz_count}개로 시작합니다."


def data_loaded(quiz_count: int, best_score: int) -> str:
    return f"📂 저장된 데이터를 불러왔습니다. (퀴즈 {quiz_count}개, 최고점수 {best_score}점)"
