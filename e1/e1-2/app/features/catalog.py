"""퀴즈 목록/추가/수정/삭제를 담당한다. 화면 입출력은 하지 않는다."""

from app.constants import CATEGORIES
from app.models.quiz import Quiz


class QuizCatalog:
    """게임이 들고 있는 퀴즈 목록을 직접 수정한다."""

    def __init__(self, quizzes: list[Quiz]) -> None:
        self.quizzes = quizzes

    def add(self, quiz: Quiz) -> None:
        self.quizzes.append(quiz)

    def replace(self, index: int, quiz: Quiz) -> None:
        self.quizzes[index] = quiz

    def remove(self, index: int) -> Quiz:
        return self.quizzes.pop(index)

    def grouped(self) -> dict[str, list[Quiz]]:
        """카테고리별로 묶은 딕셔너리를 반환한다. 카테고리 순서는 CATEGORIES를 따른다."""
        groups: dict[str, list[Quiz]] = {category: [] for category in CATEGORIES}
        for quiz in self.quizzes:
            groups.setdefault(quiz.category, []).append(quiz)
        return groups
