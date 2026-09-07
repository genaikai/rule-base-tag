"""모델 사고 중단 검출 태거.

모델이 생각 중간에 멈춘 경우를 판정한다.
"""

import re
from .base import Tagger


class ModelThinkingStoppedTagger(Tagger):
    """모델이 사고 중에 멈춘 경우를 판정하는 태거."""

    name = "model_thinking_stopped"

    THINKING_STOPPED_INDICATORS = {
        "thinking stopped",
        "stopped thinking",
        "interrupted",
        "interrupted thinking",
        "thinking halted",
        "thinking paused",
        "thought process stopped",
        "[thinking stops]",
        "[thinking stopped]",
        "[interrupted]",
        "[paused]",
    }

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 모델 사고 중단 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_thinking_stopped(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have stopped thinking",
        }

    def _has_thinking_stopped(self, row: dict) -> bool:
        """한 행에서 모델 사고 중단을 감지한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip().lower()
            if not text:
                continue

            # 명시적 지시자 확인
            for indicator in self.THINKING_STOPPED_INDICATORS:
                if indicator in text:
                    return True

            # XML 태그 형태의 사고 블록이 완료되지 않음
            if "<thinking>" in text:
                if not text.endswith("</thinking>"):
                    # 사고 블록이 시작했지만 닫혀있지 않음
                    return True

            # 특정 키워드로 끝남 (불완전한 사고)
            incomplete_patterns = [
                r"wait[,.]?\s*$",
                r"hmm[,.]?\s*$",
                r"let me think[,.]?\s*$",
                r"actually[,.]?\s*$",
                r"but[,.]?\s*$",
            ]
            for pattern in incomplete_patterns:
                if re.search(pattern, text):
                    return True

            # 응답이 완전하지 않은 신호: 단어나 문장이 완료되지 않음
            # (예: "The answer is..." 다음에 아무것도 없음)
            if text.endswith(("is", "was", "are", "were", "be", "being")):
                return True

        return False
