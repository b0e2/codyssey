"""게임 전체 흐름을 관리한다."""

from app.cli import views
from app.cli.prompts import (
    read_int,
    read_int_optional,
    read_text,
    read_text_optional,
    read_yes_no,
)
from app.constants import (
    CATEGORIES,
    CATEGORY_ALL,
    CATEGORY_BACKEND,
    CATEGORY_LABELS,
    CATEGORY_PYTHON,
    CHOICE_COUNT,
    HISTORY_DISPLAY_COUNT,
    MAX_ANSWER,
    MIN_ANSWER,
)
from app.features.catalog import QuizCatalog
from app.features.play import PlaySession, filter_by_category, prepare_quizzes
from app.features.score import ScoreService
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
        pool = filter_by_category(self.quizzes, category)
        if not pool:
            print("⚠️ 해당 카테고리에 퀴즈가 없습니다.")
            return

        count = read_int(f"문제 수 (1-{len(pool)}): ", 1, len(pool))
        quizzes = prepare_quizzes(pool, count)
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

        service = ScoreService(self.board)
        is_best = service.record_play(
            category,
            session.total,
            session.correct,
            session.score(),
            session.hints_used,
        )
        if is_best:
            print("🏆 새로운 최고 점수입니다!")

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
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return

        print("\n🗑️ 퀴즈 삭제")
        print(views.quiz_picker(self.quizzes))
        index = read_int("삭제할 번호: ", 1, len(self.quizzes)) - 1
        quiz = self.quizzes[index]

        print(f"\n선택한 문제: {quiz.question}")
        if not read_yes_no("정말 삭제하시겠습니까? (y/n): "):
            print("삭제를 취소했습니다.")
            return

        QuizCatalog(self.quizzes).remove(index)
        print("🗑️ 퀴즈가 삭제되었습니다.")

    def _score(self) -> None:
        if not self.board.records:
            print("\n🏆 아직 푼 기록이 없습니다. 퀴즈를 먼저 풀어 보세요.")
            return

        service = ScoreService(self.board)
        recent = service.recent_records(HISTORY_DISPLAY_COUNT)
        print()
        print(views.score_board(self.board, recent, CATEGORY_LABELS))
