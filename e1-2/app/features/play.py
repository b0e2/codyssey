"""퀴즈 출제와 채점을 담당한다. 화면 입출력은 하지 않는다."""

import random

from app.constants import CATEGORY_ALL
from app.models.quiz import Quiz


def filter_by_category(quizzes: list[Quiz], category: str) -> list[Quiz]:
    """카테고리로 퀴즈를 걸러낸다. CATEGORY_ALL이면 전체를 그대로 돌려준다."""
    if category == CATEGORY_ALL:
        return list(quizzes)
    return [quiz for quiz in quizzes if quiz.category == category]


def prepare_quizzes(quizzes: list[Quiz], count: int, shuffle: bool = False) -> list[Quiz]:
    """출제 목록을 만든다. shuffle이 참이면 섞은 뒤 count개를 고른다."""
    ordered = list(quizzes)
    if shuffle:
        random.shuffle(ordered)
    return ordered[:count]


class PlaySession:
    """한 번의 풀이 진행 상태(현재 문제, 정답 수, 힌트 수)를 관리한다."""

    def __init__(self, quizzes: list[Quiz]) -> None:
        self.quizzes = quizzes
        self.total = len(quizzes)
        self.correct = 0
        self.hints_used = 0
        self._index = 0
        self._earned = 0.0
        self._current_hinted = False

    def current(self) -> Quiz | None:
        """지금 풀 문제를 반환한다. 다 풀었으면 None."""
        if self._index >= self.total:
            return None
        return self.quizzes[self._index]

    def position(self) -> int:
        """현재 문제의 표시용 번호(1부터)."""
        return self._index + 1

    def reveal_hint(self) -> str | None:
        """현재 문제의 힌트를 반환한다. 힌트가 있으면 이 문항을 힌트 사용으로 표시한다."""
        quiz = self.quizzes[self._index]
        if quiz.hint and not self._current_hinted:
            self._current_hinted = True
            self.hints_used += 1
        return quiz.hint

    def submit(self, number: int) -> bool:
        """현재 문제에 답하고 정답 여부를 반환한 뒤 다음 문제로 넘어간다."""
        quiz = self.quizzes[self._index]
        correct = quiz.is_correct(number)
        if correct:
            # 힌트를 본 문항은 배점의 50%만 얻는다.
            self._earned += 0.5 if self._current_hinted else 1.0
            self.correct += 1
        self._index += 1
        self._current_hinted = False
        return correct

    def score(self) -> int:
        """100점 만점 기준으로 점수를 계산한다. 힌트 차감이 반영된다."""
        if self.total == 0:
            return 0
        return round(self._earned / self.total * 100)
