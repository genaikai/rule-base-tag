"""검색 질의가 만들어지지 않았는가.

**필드 하나만 본다.** 이전 판은 행에 빈 값이 하나라도 있으면 켰는데, 그러면
답변이 비어 있는 행까지 "검색 질의가 없다" 로 세어진다.
"""

from ...contracts import SEARCH_QUERY
from .._shared import tally

NAME = "empty_search_query"

EMPTY_TOKENS = frozenset({"", "-", "[]", '""', "''", "none", "null", "n/a", "없음"})


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(SEARCH_QUERY) or "").strip()
    return text.lower() in EMPTY_TOKENS
