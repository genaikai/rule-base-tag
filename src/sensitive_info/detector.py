"""민감정보 포함 검출 태거.

개인정보(이메일, 전화, 주민등록번호), 보안정보(API 키, 암호) 등을 감지한다.
"""

import re
from src.framework.base import Tagger


class SensitiveInfoTagger(Tagger):
    """민감정보 포함 여부를 판정하는 태거."""

    name = "sensitive_info"

    # 민감정보 패턴들. 필요에 따라 추가/수정
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(?:\+?\d{1,3}[-.\s]?)?\(?(?:\d{2,3})\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
        "ssn": r"\d{2,4}[-.]?\d{2,4}[-.]?\d{2,4}",  # 주민등록번호 형태
        "credit_card": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
        "api_key": r"(?:api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*['\"]?[\w\-]{20,}['\"]?",
        "password": r"(?:password|passwd|pwd)\s*[:=]\s*['\"].*?['\"]",
        "arn": r"arn:[\w\-:]+",  # AWS ARN
        "url_with_auth": r"https?://[^:]+:[^@]+@",  # URL에 인증정보 포함
    }

    def tag(self, rows: list[dict]) -> dict:
        """각 행에 민감정보 포함 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_sensitive_info(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows contain sensitive information",
        }

    def _has_sensitive_info(self, row: dict) -> bool:
        """한 행의 모든 문자열 필드를 검사하고 민감정보가 있는지 판정한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            # 여러 패턴을 검사
            for pattern in self.PATTERNS.values():
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        return False
