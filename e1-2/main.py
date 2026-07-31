"""파이썬 퀴즈 게임 엔트리포인트."""

from app.cli.prompts import ExitRequested
from app.game import QuizGame


def main() -> None:
    game = QuizGame()
    try:
        game.run()
    except ExitRequested:
        pass
    print("👋 게임을 종료합니다.")


if __name__ == "__main__":
    main()
