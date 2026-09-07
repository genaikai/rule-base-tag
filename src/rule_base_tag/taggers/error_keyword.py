"""에러 키워드 검출 태거.

답변에 오류나 예외를 나타내는 키워드가 포함되어 있는지 검사한다.
"""

import re
from .base import Tagger


class ErrorKeywordTagger(Tagger):
    """답변의 오류 키워드 포함 여부를 판정하는 태거."""

    name = "error_keyword"

    ERROR_KEYWORDS = {
        "error",
        "exception",
        "failed",
        "failure",
        "crash",
        "crashed",
        "bug",
        "wrong",
        "incorrect",
        "invalid",
        "null",
        "undefined",
        "traceback",
        "oops",
        "sorry",
        "mistake",
        "fault",
    }

    def tag(self, rows: list[dict]) -> dict:
        """각 행에 에러 키워드 포함 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_error_keyword(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows contain error keywords",
        }

    def _has_error_keyword(self, row: dict) -> bool:
        """한 행의 모든 문자열 필드에서 에러 키워드를 검색한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip().lower()
            if not text:
                continue
            for keyword in self.ERROR_KEYWORDS:
                if re.search(r"\b" + re.escape(keyword) + r"\b", text):
                    return True
        return False
