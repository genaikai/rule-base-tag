"""검색 쿼리 없음 검출 태거.

검색 쿼리가 비어있거나 생성되지 않은 경우를 판정한다.
"""

from .base import Tagger


class EmptySearchQueryTagger(Tagger):
    """검색 쿼리가 비어있는지 판정하는 태거."""

    name = "empty_search_query"

    EMPTY_INDICATORS = {
        "no query",
        "empty query",
        "query is empty",
        "no search query",
        "search query is empty",
        "[]",
        '""',
        "''",
    }

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 검색 쿼리 없음 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_empty_query(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have empty search query",
        }

    def _has_empty_query(self, row: dict) -> bool:
        """한 행에서 검색 쿼리 없음을 감지한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                # 완전히 빈 필드는 검색 쿼리가 없는 것과 같음
                return True

            text_lower = text.lower()

            # 명시적으로 빈 쿼리를 나타내는 지시자 확인
            for indicator in self.EMPTY_INDICATORS:
                if indicator in text_lower:
                    return True

        return False
