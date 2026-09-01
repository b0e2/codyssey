"""파이썬 퀴즈 게임 엔트리포인트."""

from app.cli.prompts import ExitRequested
from app.game import QuizGame
from app.storage.repository import StateRepository


def main() -> None:
    repository = StateRepository()
    game = QuizGame(repository)
    try:
        game.run()
    except ExitRequested:
        pass
    game.save()
    print("👋 게임을 종료합니다.")


if __name__ == "__main__":
    main()
