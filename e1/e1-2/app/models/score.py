"""점수 기록과 최고 점수판을 표현하는 도메인 모델."""

from app.constants import CATEGORIES, HISTORY_LIMIT


class ScoreRecord:
    """한 번의 게임 결과 한 건을 담는다."""

    def __init__(
        self,
        played_at: str,
        category: str,
        total: int,
        correct: int,
        score: int,
        hints_used: int,
    ) -> None:
        self.played_at = played_at
        self.category = category
        self.total = total
        self.correct = correct
        self.score = score
        self.hints_used = hints_used

    def to_dict(self) -> dict:
        return {
            "played_at": self.played_at,
            "category": self.category,
            "total": self.total,
            "correct": self.correct,
            "score": self.score,
            "hints_used": self.hints_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoreRecord":
        if not isinstance(data, dict):
            raise ValueError("기록 항목이 딕셔너리가 아닙니다.")
        return cls(
            played_at=str(data.get("played_at", "")),
            category=str(data.get("category", "")),
            total=int(data.get("total", 0)),
            correct=int(data.get("correct", 0)),
            score=int(data.get("score", 0)),
            hints_used=int(data.get("hints_used", 0)),
        )


class ScoreBoard:
    """전체 최고점, 카테고리별 최고점, 최근 기록 목록을 관리한다."""

    def __init__(
        self,
        best_score: int = 0,
        best_by_category: dict[str, int] | None = None,
        records: list[ScoreRecord] | None = None,
    ) -> None:
        self.best_score = best_score
        self.best_by_category = best_by_category or {}
        self.records = records or []

    def add_record(self, record: ScoreRecord) -> None:
        """기록을 추가하고 최근 HISTORY_LIMIT건만 남긴다."""
        self.records.append(record)
        if len(self.records) > HISTORY_LIMIT:
            self.records = self.records[-HISTORY_LIMIT:]

    def to_dict(self) -> dict:
        return {
            "best_score": self.best_score,
            "best_by_category": dict(self.best_by_category),
            "history": [record.to_dict() for record in self.records],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoreBoard":
        best_score = data.get("best_score", 0)
        if not isinstance(best_score, int) or isinstance(best_score, bool):
            raise ValueError("best_score가 정수가 아닙니다.")

        best_by_category = cls._clean_best_by_category(data.get("best_by_category"))

        history = data.get("history", [])
        if not isinstance(history, list):
            raise ValueError("history가 리스트가 아닙니다.")
        records = [ScoreRecord.from_dict(item) for item in history]

        return cls(best_score, best_by_category, records)

    @staticmethod
    def _clean_best_by_category(raw: object) -> dict[str, int]:
        """값이 없거나 형식이 이상하면 빈 딕셔너리로 복구한다.

        필수 필드가 아니므로 이것만으로 전체를 초기화하지 않고 조용히 걸러낸다.
        """
        if not isinstance(raw, dict):
            return {}
        cleaned: dict[str, int] = {}
        for category, value in raw.items():
            if category in CATEGORIES and isinstance(value, int) and not isinstance(value, bool):
                cleaned[category] = value
        return cleaned
