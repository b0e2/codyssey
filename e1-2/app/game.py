"""게임 전체 흐름을 관리한다."""

from app.cli import views
from app.cli.prompts import read_int
from app.constants import (
    CATEGORIES,
    CATEGORY_ALL,
    CATEGORY_BACKEND,
    CATEGORY_LABELS,
    CATEGORY_PYTHON,
    MAX_ANSWER,
    MIN_ANSWER,
)
from app.features.catalog import QuizCatalog
from app.features.play import PlaySession, filter_by_category
from app.models.score import ScoreBoard
from app.storage.repository import LOAD_CREATED, LOAD_RECOVERED, StateRepository

MENU_LABELS = {
    1: "퀴즈 풀기",
    2: "퀴즈 추가",
    3: "퀴즈 목록",
    4: "퀴즈 수정",
    5: "퀴즈 삭제",
    6: "점수 확인",
    7: "종료",
}


class QuizGame:
    """메뉴를 표시하고 각 기능으로 흐름을 분배한다."""

    def __init__(self, repository: StateRepository) -> None:
        self.repository = repository
        self.quizzes = []
        self.board = ScoreBoard()

    def run(self) -> None:
        self._load()
        while True:
            handlers = self._handlers()
            print()
            print(views.menu(MENU_LABELS))
            choice = read_int("선택: ", 1, len(MENU_LABELS))
            handler = handlers[choice]
            if handler is None:
                break
            handler()

    def save(self) -> None:
        self.repository.save(self.quizzes, self.board)

    def _load(self) -> None:
        state = self.repository.load()
        self.quizzes = state.quizzes
        self.board = state.board
        print(views.title(CATEGORIES, CATEGORY_LABELS))
        if state.status == LOAD_CREATED:
            print(views.data_created(len(self.quizzes)))
        elif state.status == LOAD_RECOVERED:
            print(views.data_recovered(len(self.quizzes)))
        else:
            print(views.data_loaded(len(self.quizzes), self.board.best_score))

    def _handlers(self) -> dict:
        return {
            1: self._play,
            2: self._add,
            3: self._list,
            4: self._edit,
            5: self._delete,
            6: self._score,
            7: None,
        }

    def _play(self) -> None:
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return

        print("\n❓ 퀴즈 풀기")
        category = self._select_category()
        quizzes = filter_by_category(self.quizzes, category)
        if not quizzes:
            print("⚠️ 해당 카테고리에 퀴즈가 없습니다.")
            return

        session = PlaySession(quizzes)
        while True:
            quiz = session.current()
            if quiz is None:
                break
            print()
            print(views.quiz_question(session.position(), session.total, quiz))
            number = read_int("정답 입력 (1-4): ", MIN_ANSWER, MAX_ANSWER)
            correct = session.submit(number)
            print(views.answer_feedback(correct, quiz.answer))

        print()
        print(views.play_result(session.correct, session.total, session.score()))

    def _select_category(self) -> str:
        print(
            views.category_menu(
                CATEGORY_LABELS[CATEGORY_PYTHON],
                CATEGORY_LABELS[CATEGORY_BACKEND],
            )
        )
        choice = read_int("선택: ", 1, 3)
        return {1: CATEGORY_PYTHON, 2: CATEGORY_BACKEND, 3: CATEGORY_ALL}[choice]

    def _add(self) -> None:
        print("(준비 중) 퀴즈 추가")

    def _list(self) -> None:
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return
        catalog = QuizCatalog(self.quizzes)
        print()
        print(views.quiz_list(catalog.grouped(), CATEGORY_LABELS, len(self.quizzes)))

    def _edit(self) -> None:
        print("(준비 중) 퀴즈 수정")

    def _delete(self) -> None:
        print("(준비 중) 퀴즈 삭제")

    def _score(self) -> None:
        print("(준비 중) 점수 확인")
