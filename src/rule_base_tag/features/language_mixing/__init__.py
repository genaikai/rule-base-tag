"""한 답변 안에 문자 체계가 둘 이상 섞였는가.

질문과 답변을 견주는 language_mismatch 와 다르다. 이쪽은 답변 하나만 본다.
"""

from ...schema import ANSWER
from .._shared import tally, scripts_in

NAME = "language_mixing"


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(ANSWER) or "").strip()
    return len(scripts_in(text)) > 1 if text else False
