"""게임 전체 흐름을 관리한다."""

from app.constants import CATEGORIES, CATEGORY_LABELS


class QuizGame:
    """메뉴를 표시하고 각 기능으로 흐름을 분배한다."""

    def run(self) -> None:
        print("=" * 40)
        print("        🐍 파이썬 퀴즈 게임 🐍")
        print("=" * 40)
        for category in CATEGORIES:
            print(f"  - {CATEGORY_LABELS[category]}")
        print("=" * 40)
        # TODO : 기능 분배 