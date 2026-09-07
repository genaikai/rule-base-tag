"""검색 결과 없음 검출 태거.

검색하여 가져온 문서가 없거나 비어있는 경우를 판정한다.
"""

from .base import Tagger


class EmptyRetrievedDocsTagger(Tagger):
    """검색 결과 문서가 비어있는지 판정하는 태거."""

    name = "empty_retrieved_docs"

    EMPTY_INDICATORS = {
        "no documents found",
        "no results",
        "no matching documents",
        "empty",
        "none",
        "null",
        "[]",
        "{}",
    }

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 검색 결과 없음 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_empty_docs(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have no retrieved documents",
        }

    def _has_empty_docs(self, row: dict) -> bool:
        """한 행에서 검색 결과 없음을 감지한다.

        현재는 특정 필드명을 가정하지 않고, 모든 값을 검사한다.
        실제 데이터에서는 'retrieved_docs', 'search_result' 같은 필드를 명시적으로 검사하도록 수정할 수 있다.
        """
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip().lower()
            if not text:
                continue

            # 빈 결과를 나타내는 지시자 확인
            for indicator in self.EMPTY_INDICATORS:
                if indicator in text:
                    return True

            # 숫자 0개 또는 []처럼 보이는 패턴
            if text in ("[]", "{}", "0 results", "0 documents"):
                return True

        return False
