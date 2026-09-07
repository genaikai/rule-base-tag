"""답변에 오류를 드러내는 낱말이 있는가."""

import re

from ...contracts import ANSWER
from .._shared import tally

NAME = "error_keyword"

# 낱말 단위로 본다. 부분 문자열로 보면 "errorless" 나 "buggy" 까지 걸린다.
KEYWORDS_EN = (
    "error", "errors", "exception", "failed", "failure", "crash", "crashed",
    "bug", "wrong", "incorrect", "invalid", "undefined", "traceback",
)
# 한글에는 낱말 경계(\b)가 안 먹는다 — 조사가 붙으면 "오류가" 를 놓친다.
# 그래서 이쪽만 부분 문자열로 본다. 목록을 하나로 합치지 마라
KEYWORDS_KO = ("오류", "실패", "예외", "잘못")

_PAT = re.compile(r"\b(?:" + "|".join(KEYWORDS_EN) + r")\b", re.IGNORECASE)


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(ANSWER) or "").strip()
    if not text:
        return False
    return bool(_PAT.search(text)) or any(word in text for word in KEYWORDS_KO)
