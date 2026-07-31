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


def data_recovered(quiz_count: int) -> str:
    return f"⚠️ 저장 파일이 손상되어 기본 퀴즈 {quiz_count}개로 복구했습니다."


def category_menu(python_label: str, backend_label: str) -> str:
    lines = [
        "카테고리",
        f"  1. {python_label}",
        f"  2. {backend_label}",
        "  3. 전체",
    ]
    return "\n".join(lines)


def quiz_question(position: int, total: int, quiz) -> str:
    lines = [
        f"[문제 {position}/{total}]",
        quiz.question,
        quiz.format_choices(),
    ]
    return "\n".join(lines)


def answer_feedback(correct: bool, answer: int) -> str:
    if correct:
        return "⭕ 정답입니다!"
    return f"❌ 오답입니다. 정답은 {answer}번입니다."


def play_result(correct: int, total: int, score: int) -> str:
    return f"🏆 결과: {total}문제 중 {correct}문제 정답 ({score}점)"
