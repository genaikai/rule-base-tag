"""질문과 답변의 언어가 다른가.

한쪽이라도 언어를 가릴 수 없으면 **켜지 않는다.** 숫자·기호뿐인 답변을 두고
"언어가 다르다" 고 하면 그건 판정이 아니라 잡음이다.
"""

from ...schema import ANSWER, QUERY
from .._shared import dominant_script, tally

NAME = "language_mismatch"


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    asked = dominant_script((row.get(QUERY) or "").strip())
    answered = dominant_script((row.get(ANSWER) or "").strip())
    if asked is None or answered is None:
        return False
    return asked != answered
