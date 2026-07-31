"""게임 전체 흐름을 관리한다."""

from app.cli import views
from app.cli.prompts import read_int
from app.constants import CATEGORIES, CATEGORY_LABELS
from app.models.score import ScoreBoard
from app.storage.repository import LOAD_CREATED, StateRepository

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
        print("(준비 중) 퀴즈 풀기")

    def _add(self) -> None:
        print("(준비 중) 퀴즈 추가")

    def _list(self) -> None:
        print("(준비 중) 퀴즈 목록")

    def _edit(self) -> None:
        print("(준비 중) 퀴즈 수정")

    def _delete(self) -> None:
        print("(준비 중) 퀴즈 삭제")

    def _score(self) -> None:
        print("(준비 중) 점수 확인")
