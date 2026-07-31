"""state.json 파일 하나를 읽고 쓴다. 저장 시점은 호출하는 쪽이 정한다."""

import json
import os

from app.constants import STATE_PATH, TEMP_STATE_PATH
from app.models.quiz import Quiz
from app.models.score import ScoreBoard
from app.storage.defaults import default_quizzes

# 로드 결과 상태
LOAD_CREATED = "created"      # 파일이 없어 기본 데이터로 시작
LOAD_OK = "loaded"            # 정상 로드
LOAD_RECOVERED = "recovered"  # 파일이 손상되어 기본 데이터로 복구


class GameState:
    """불러온(또는 새로 만든) 퀴즈 목록과 점수판을 함께 담는다."""

    def __init__(self, quizzes: list[Quiz], board: ScoreBoard, status: str) -> None:
        self.quizzes = quizzes
        self.board = board
        self.status = status


class StateRepository:
    """state.json 로드와 저장을 담당한다."""

    def __init__(self, path=STATE_PATH, temp_path=TEMP_STATE_PATH) -> None:
        self.path = path
        self.temp_path = temp_path

    def load(self) -> GameState:
        if not self.path.exists():
            return GameState(default_quizzes(), ScoreBoard(), LOAD_CREATED)

        try:
            with open(self.path, encoding="utf-8") as file:
                data = json.load(file)
            quizzes = self._parse_quizzes(data)
            board = ScoreBoard.from_dict(data)
        except (OSError, json.JSONDecodeError, ValueError):
            return GameState(default_quizzes(), ScoreBoard(), LOAD_RECOVERED)

        return GameState(quizzes, board, LOAD_OK)

    def _parse_quizzes(self, data: dict) -> list[Quiz]:
        raw = data.get("quizzes")
        if not isinstance(raw, list):
            raise ValueError("quizzes가 리스트가 아닙니다.")
        return [Quiz.from_dict(item) for item in raw]

    def save(self, quizzes: list[Quiz], board: ScoreBoard) -> None:
        data = {"quizzes": [quiz.to_dict() for quiz in quizzes]}
        data.update(board.to_dict())
        try:
            with open(self.temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            os.replace(self.temp_path, self.path)
        except OSError as error:
            print(f"⚠️ 저장에 실패했습니다: {error}")
