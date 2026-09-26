"""퀴즈 한 문제를 표현하는 도메인 모델."""

from app.constants import CHOICE_COUNT, MIN_ANSWER, MAX_ANSWER, CATEGORIES


class Quiz:
    """문제, 선택지 4개, 정답 번호(1~4), 힌트, 카테고리를 담는다."""

    def __init__(
        self,
        question: str,
        choices: list[str],
        answer: int,
        category: str,
        hint: str | None = None,
    ) -> None:
        self.question = question
        self.choices = choices
        self.answer = answer
        self.category = category
        self.hint = hint

    def is_correct(self, number: int) -> bool:
        return number == self.answer

    def format_choices(self) -> str:
        lines = [f"  {i}. {choice}" for i, choice in enumerate(self.choices, start=1)]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
            "hint": self.hint,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quiz":
        if not isinstance(data, dict):
            raise ValueError("퀴즈 항목이 딕셔너리가 아닙니다.")

        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question이 비어 있거나 문자열이 아닙니다.")

        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) != CHOICE_COUNT:
            raise ValueError(f"choices는 {CHOICE_COUNT}개의 리스트여야 합니다.")
        if not all(isinstance(c, str) and c.strip() for c in choices):
            raise ValueError("choices 항목이 비어 있거나 문자열이 아닙니다.")

        answer = data.get("answer")
        if not isinstance(answer, int) or isinstance(answer, bool):
            raise ValueError("answer가 정수가 아닙니다.")
        if not (MIN_ANSWER <= answer <= MAX_ANSWER):
            raise ValueError(f"answer는 {MIN_ANSWER}~{MAX_ANSWER} 범위여야 합니다.")

        category = data.get("category")
        if category not in CATEGORIES:
            raise ValueError(f"category가 올바르지 않습니다: {category}")

        hint = data.get("hint")
        if hint is not None and not isinstance(hint, str):
            raise ValueError("hint는 문자열이거나 없어야 합니다.")

        return cls(question, choices, answer, category, hint)
