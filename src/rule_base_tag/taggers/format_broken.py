"""포맷 깨짐 검출 태거.

테이블이나 구조화된 포맷이 손상되었는지 판정한다.
"""

import re
from .base import Tagger


class FormatBrokenTagger(Tagger):
    """구조화된 포맷(테이블, 리스트 등)이 손상되었는지 판정하는 태거."""

    name = "format_broken"

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 포맷 손상 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_broken_format(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have broken format",
        }

    def _has_broken_format(self, row: dict) -> bool:
        """한 행의 텍스트에서 포맷 손상을 감지한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue

            # 테이블 형태가 불완전한 경우 (|가 짝이 맞지 않음)
            if "|" in text:
                lines = text.split("\n")
                pipe_counts = [line.count("|") for line in lines if line.strip()]
                if pipe_counts and len(set(pipe_counts)) > 1:
                    return True  # 행마다 파이프 개수가 다름

            # 마크다운 코드 블록이 닫혀있지 않음
            if "```" in text:
                if text.count("```") % 2 != 0:
                    return True

            # JSON/XML 괄호 불균형
            if self._has_unbalanced_brackets(text):
                return True

        return False

    def _has_unbalanced_brackets(self, text: str) -> bool:
        """괄호의 균형을 확인한다."""
        pairs = {"[": "]", "{": "}", "(": ")"}
        stack = []
        for char in text:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack or pairs[stack.pop()] != char:
                    return True  # 불균형
        return bool(stack)  # 닫혀있지 않은 괄호 있음
