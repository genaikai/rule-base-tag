"""답변 잘림 검출 태거.

답변이 중간에 끊겼는지 판정한다.
"""

from src.framework.base import Tagger


class AnswerTruncatedTagger(Tagger):
    """답변이 불완전하게 끝나는지 판정하는 태거."""

    name = "answer_truncated"

    TRUNCATION_INDICATORS = {
        "...",
        "....",
        " ...",
        "[incomplete]",
        "[truncated]",
        "[cut off]",
        "[more]",
    }

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 답변 잘림 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._is_truncated(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have truncated answers",
        }

    def _is_truncated(self, row: dict) -> bool:
        """한 행의 모든 문자열 필드에서 잘림 신호를 검색한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            # 끝이 "..."로 끝나거나, 특정 잘림 지시자가 포함되는지 확인
            if text.endswith("...") or text.endswith("...."):
                return True
            for indicator in self.TRUNCATION_INDICATORS:
                if indicator in text:
                    return True
        return False
