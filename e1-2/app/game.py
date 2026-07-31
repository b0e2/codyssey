"""게임 전체 흐름을 관리한다."""

from app.cli import views
from app.cli.prompts import read_int, read_int_optional, read_text, read_text_optional
from app.constants import (
    CATEGORIES,
    CATEGORY_ALL,
    CATEGORY_BACKEND,
    CATEGORY_LABELS,
    CATEGORY_PYTHON,
    CHOICE_COUNT,
    MAX_ANSWER,
    MIN_ANSWER,
)
from app.features.catalog import QuizCatalog
from app.features.play import PlaySession, filter_by_category
from app.models.quiz import Quiz
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
            self.save()

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
        print("\n✅ 퀴즈 추가")
        question = read_text("문제: ")
        choices = [read_text(f"선택지 {i}: ") for i in range(1, CHOICE_COUNT + 1)]
        answer = read_int(f"정답 번호 ({MIN_ANSWER}-{MAX_ANSWER}): ", MIN_ANSWER, MAX_ANSWER)
        category = self._select_quiz_category()
        hint = read_text_optional("힌트 (없으면 Enter): ") or None

        quiz = Quiz(question, choices, answer, category, hint)
        QuizCatalog(self.quizzes).add(quiz)
        print("✅ 퀴즈가 추가되었습니다.")

    def _select_quiz_category(self) -> str:
        print(
            views.category_menu(
                CATEGORY_LABELS[CATEGORY_PYTHON],
                CATEGORY_LABELS[CATEGORY_BACKEND],
                include_all=False,
            )
        )
        choice = read_int("카테고리 선택: ", 1, 2)
        return {1: CATEGORY_PYTHON, 2: CATEGORY_BACKEND}[choice]

    def _list(self) -> None:
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return
        catalog = QuizCatalog(self.quizzes)
        print()
        print(views.quiz_list(catalog.grouped(), CATEGORY_LABELS, len(self.quizzes)))

    def _edit(self) -> None:
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return

        print("\n✏️ 퀴즈 수정")
        print(views.quiz_picker(self.quizzes))
        index = read_int("수정할 번호: ", 1, len(self.quizzes)) - 1
        quiz = self.quizzes[index]

        print()
        print(views.quiz_detail(quiz, CATEGORY_LABELS))
        print("\n(빈 입력은 기존 값 유지)")

        question = read_text_optional(f"문제 [{quiz.question}]: ") or quiz.question
        choices = []
        for order, current in enumerate(quiz.choices, start=1):
            value = read_text_optional(f"선택지 {order} [{current}]: ") or current
            choices.append(value)

        answer = read_int_optional(
            f"정답 번호 ({MIN_ANSWER}-{MAX_ANSWER}) [{quiz.answer}]: ", MIN_ANSWER, MAX_ANSWER
        )
        if answer is None:
            answer = quiz.answer

        category = self._edit_quiz_category(quiz.category)

        hint_input = read_text_optional(f"힌트 [{quiz.hint or '없음'}]: ")
        hint = quiz.hint if hint_input == "" else hint_input

        updated = Quiz(question, choices, answer, category, hint)
        QuizCatalog(self.quizzes).replace(index, updated)
        print("✏️ 퀴즈가 수정되었습니다.")

    def _edit_quiz_category(self, current: str) -> str:
        print(
            views.category_menu(
                CATEGORY_LABELS[CATEGORY_PYTHON],
                CATEGORY_LABELS[CATEGORY_BACKEND],
                include_all=False,
            )
        )
        choice = read_int_optional("카테고리 (Enter=유지): ", 1, 2)
        if choice is None:
            return current
        return {1: CATEGORY_PYTHON, 2: CATEGORY_BACKEND}[choice]

    def _delete(self) -> None:
        print("(준비 중) 퀴즈 삭제")

    def _score(self) -> None:
        print("(준비 중) 점수 확인")
