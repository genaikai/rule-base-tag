"""유효하지 않은 링크 검출 태거.

제시된 링크의 형식이 유효하지 않거나 문법 오류가 있는 경우를 판정한다.
"""

import re
from .base import Tagger


class InvalidLinkTagger(Tagger):
    """제시된 링크의 유효성을 판정하는 태거."""

    name = "invalid_link"

    # 유효한 URL 패턴
    VALID_URL_PATTERN = re.compile(
        r"https?://[^\s<>\"{}|\\^`\[\]]*[^\s<>\"{}|\\^`\[\].,:;!?\'\")]"
    )

    # 마크다운 링크 패턴
    MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def tag(self, rows: list[dict]) -> dict:
        """각 행의 유효하지 않은 링크 여부를 판정한다."""
        flagged_indices = []

        for i, row in enumerate(rows):
            if self._has_invalid_link(row):
                flagged_indices.append(i)

        return {
            "count": len(flagged_indices),
            "rows": flagged_indices,
            "note": f"{len(flagged_indices)}/{len(rows)} rows have invalid links",
        }

    def _has_invalid_link(self, row: dict) -> bool:
        """한 행의 링크 유효성을 검사한다."""
        for value in row.values():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue

            # 링크가 있는지 확인
            if "http" in text or "[" in text and "]" in text and "(" in text:
                if self._has_broken_link(text):
                    return True

        return False

    def _has_broken_link(self, text: str) -> bool:
        """텍스트에서 깨진 링크를 검사한다."""
        # 마크다운 링크 검사: [텍스트](URL)
        markdown_links = self.MARKDOWN_LINK_PATTERN.findall(text)
        for link_text, url in markdown_links:
            if not url or not self._is_valid_url(url):
                return True
            # URL이 http(s)로 시작하지 않으면 유효하지 않음
            if not url.startswith("http://") and not url.startswith("https://"):
                return True

        # 일반 URL 검사
        if "http" in text:
            # URL이 불완전하게 끝남 (예: "http://example.com...")
            if text.rstrip().endswith("..."):
                return True
            # URL에 특수문자가 제대로 이스케이프되지 않음
            if "http://" in text or "https://" in text:
                urls = re.findall(r"https?://\S+", text)
                for url in urls:
                    # URL 끝에 구두점이 붙어있으면 무효
                    if url.rstrip(".,;:!?)") != url:
                        continue  # 구두점 제거 후 다시 검사
                    # 괄호가 닫혀있지 않음
                    if url.count("(") != url.count(")"):
                        return True

        return False

    def _is_valid_url(self, url: str) -> bool:
        """URL의 기본 형식이 유효한지 확인한다."""
        if not url:
            return False
        # http(s)로 시작하거나, 상대 경로(/)로 시작
        if url.startswith("http://") or url.startswith("https://") or url.startswith("/"):
            return True
        return False
