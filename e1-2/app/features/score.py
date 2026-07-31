"""최고 점수 갱신과 기록 관리를 담당한다. 화면 입출력은 하지 않는다."""

from datetime import datetime

from app.constants import CATEGORY_ALL
from app.models.score import ScoreBoard, ScoreRecord


class ScoreService:
    """점수판(ScoreBoard)에 기록을 남기고 최고점을 갱신한다."""

    def __init__(self, board: ScoreBoard) -> None:
        self.board = board

    def record_play(
        self,
        category: str,
        total: int,
        correct: int,
        score: int,
        hints_used: int,
    ) -> bool:
        """한 회차 결과를 기록하고 최고점을 갱신한다. 새 최고점이면 True."""
        record = ScoreRecord(
            played_at=datetime.now().isoformat(timespec="seconds"),
            category=category,
            total=total,
            correct=correct,
            score=score,
            hints_used=hints_used,
        )
        self.board.add_record(record)

        is_best = score > self.board.best_score
        if is_best:
            self.board.best_score = score

        # "전체"로 푼 회차는 카테고리별 최고점에 반영하지 않는다.
        if category != CATEGORY_ALL:
            previous = self.board.best_by_category.get(category, 0)
            if score > previous:
                self.board.best_by_category[category] = score

        return is_best

    def recent_records(self, count: int) -> list[ScoreRecord]:
        """최근 기록을 최신순으로 반환한다."""
        return list(reversed(self.board.records[-count:]))
