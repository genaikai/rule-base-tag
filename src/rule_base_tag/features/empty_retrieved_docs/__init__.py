"""검색해 온 문서가 없는가.

**필드 하나만 본다.** 이전 판은 행의 모든 값에서 "none"·"empty" 를 부분 문자열로
찾았는데, 그러면 "None of the documents matched" 같은 정상 답변도 걸린다.
"""

import re

from ...contracts import RETRIEVED_DOCS
from .._shared import tally

NAME = "empty_retrieved_docs"

# 값 전체가 이것들 중 하나면 비어 있는 것으로 본다 (부분 일치가 아니다)
EMPTY_TOKENS = frozenset({"", "-", "[]", "{}", "none", "null", "n/a", "na",
                          "no results", "no documents", "없음"})
_COUNT = re.compile(r"^\s*0+\s*(?:건|개|docs?|documents?|results?)?\s*$", re.IGNORECASE)


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    raw = row.get(RETRIEVED_DOCS)
    text = (raw or "").strip()
    return text.lower() in EMPTY_TOKENS or bool(_COUNT.match(text))
