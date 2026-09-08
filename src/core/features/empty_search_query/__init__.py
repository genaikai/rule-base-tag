"""검색 질의가 만들어지지 않았는가.

**필드 하나만 본다.** 이전 판은 행에 빈 값이 하나라도 있으면 켰는데, 그러면
답변이 비어 있는 행까지 "검색 질의가 없다" 로 세어진다.
"""

from ...schema import SEARCH_QUERY
from .._shared import ABSENT, column_missing, tally

NAME = "empty_search_query"

EMPTY_TOKENS = frozenset({"", "-", "[]", '""', "''", "none", "null", "n/a", "없음"})


def process_data(rows: list[dict]) -> dict:
    # 이 컬럼은 아직 로그에 없다. 세는 대신 못 봤다고 말한다 — 코드는 컬럼이
    # 붙는 날 그대로 살아난다.
    if column_missing(rows, SEARCH_QUERY):
        return {NAME: ABSENT}
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(SEARCH_QUERY) or "").strip()
    return text.lower() in EMPTY_TOKENS
