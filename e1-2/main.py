"""파이썬 퀴즈 게임 엔트리포인트."""

from app.game import QuizGame


def main() -> None:
    QuizGame().run()


if __name__ == "__main__":
    main()