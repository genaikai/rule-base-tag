"""생각하다 멈춰 답변을 받지 못했는가.

질문은 있는데 답변이 없는 경우가 이 판정의 본체다. 남은 둘(안 닫힌 생각 블록,
접속사로 끊긴 끝)은 답변이 오다 만 경우인데, 이쪽은 실제 로그를 봐야 꼴을 안다.
"""

import re

from ...schema import ANSWER, QUERY
from .._shared import tally

NAME = "model_thinking_stopped"

_OPEN_THINKING = re.compile(r"<think(?:ing)?>", re.IGNORECASE)
_CLOSE_THINKING = re.compile(r"</think(?:ing)?>", re.IGNORECASE)
# 접속사로 끝나면 이어질 말이 잘린 것이다
_DANGLING = re.compile(r"(?:wait|hmm|actually|but|so|그런데|하지만|그래서)[\s,]*$",
                       re.IGNORECASE)


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    answer = (row.get(ANSWER) or "").strip()
    if not answer:
        # 질문도 없으면 그건 빈 행이지 멈춘 것이 아니다
        return bool((row.get(QUERY) or "").strip())
    opened = len(_OPEN_THINKING.findall(answer))
    if opened > len(_CLOSE_THINKING.findall(answer)):
        return True
    return bool(_DANGLING.search(answer))
