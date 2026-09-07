"""질문과 답변 언어 불일치 검출 태거.

질문의 언어와 답변의 언어가 일치하지 않는 경우를 판정한다.
"""

import re
from .base import Tagger


class LanguageMismatchTagger(Tagger):
    """질문과 답변의 언어가 불일치하는지 판정하는 태거."""

    name = "language_mismatch"

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 질문-답변 언어 불일치 여부를 판정한다.

        현재는 'query'와 'answer' 필드를 찾아 비교한다.
        실제 데이터 스키마에 맞게 조정 필요.
        """
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_language_mismatch(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have language mismatch",
        }

    def _has_language_mismatch(self, row: dict) -> bool:
        """질문과 답변의 주된 언어를 비교한다."""
        # 'query'와 'answer' 필드를 찾는다 (대소문자 무시)
        query_text = None
        answer_text = None

        for key, value in row.items():
            key_lower = key.lower()
            if "query" in key_lower and query_text is None:
                query_text = str(value).strip() if value else ""
            if "answer" in key_lower and answer_text is None:
                answer_text = str(value).strip() if value else ""

        # 두 필드가 없으면 판정할 수 없음
        if not query_text or not answer_text:
            return False

        query_lang = self._detect_primary_language(query_text)
        answer_lang = self._detect_primary_language(answer_text)

        # 둘 다 감지되고 다르면 불일치
        return query_lang and answer_lang and query_lang != answer_lang

    def _detect_primary_language(self, text: str) -> str | None:
        """텍스트의 주된 언어를 감지한다."""
        if not text:
            return None

        # 각 언어의 문자 비중 계산
        korean_count = len(re.findall(r"[가-힯]", text))
        english_count = len(re.findall(r"[a-zA-Z]", text))
        cjk_count = len(re.findall(r"[一-鿿぀-ゟ゠-ヿ]", text))

        # 가장 많은 문자의 언어를 반환
        scores = {
            "korean": korean_count,
            "english": english_count,
            "cjk": cjk_count,
        }
        max_lang = max(scores, key=scores.get)

        # 임계값 이상이면 그 언어로 판정
        max_count = scores[max_lang]
        if max_count > len(text) * 0.1:  # 10% 이상
            return max_lang

        return None
