"""언어 혼합 검출 태거.

답변에 여러 언어가 섞여있는지 판정한다.
"""

import re
from src.base import Tagger


class LanguageMixingTagger(Tagger):
    """텍스트에 여러 언어가 혼합되어 있는지 판정하는 태거."""

    name = "language_mixing"

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 언어 혼합 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_language_mixing(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have mixed languages",
        }

    def _has_language_mixing(self, row: dict) -> bool:
        """한 행의 텍스트에서 언어 혼합을 감지한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue

            # 한글, 중국어/일본어, 라틴 문자, 키릴 문자 등의 존재 여부 확인
            has_korean = bool(re.search(r"[가-힯]", text))  # 한글
            has_cjk = bool(re.search(r"[一-鿿぀-ゟ゠-ヿ]", text))  # CJK
            has_latin = bool(re.search(r"[a-zA-Z]", text))
            has_cyrillic = bool(re.search(r"[Ѐ-ӿ]", text))  # 키릴 문자
            has_arabic = bool(re.search(r"[؀-ۿ]", text))  # 아랍어

            lang_count = sum(
                [has_korean, has_cjk, has_latin, has_cyrillic, has_arabic]
            )
            if lang_count > 1:
                return True

        return False
