"""답변이 중간에 끊겼는가.

빈 답변은 여기서 잡지 않는다 — 그건 답변을 아예 못 받은 것이라
model_thinking_stopped 의 몫이다. 둘 다 켜지면 어느 쪽인지 알 수 없어진다.
"""

import re

from ...schema import ANSWER
from .._shared import tally

NAME = "answer_truncated"

MARKERS = ("[truncated]", "[incomplete]", "[cut off]", "[더보기]")
# 산문이 문장으로 안 맺힌 경우. 정상 답변은 이 중 하나로 끝난다.
# `}` 와 `>` 가 빠져 있어서 유효한 JSON 답변이 100% 잘림으로 세어졌고, `</div>` 로
# **제대로 닫은** HTML 이 벌을 받았다 — 닫는 기호는 빠짐없이 넣어야 한다.
CLOSERS = (".", "!", "?", "다", "요", "음", "」", "”", '"', ")", "]", "}", ">")
# 표·목록·코드블록은 문장부호로 끝나지 않는 것이 정상이다. 이 검사를 그대로
# 들이대면 표로 답한 행이 전부 잘림으로 잡힌다 — 합성 데이터에서 실제로 그랬다.
_STRUCTURED = re.compile(r"^\s*(?:[|\-*>+]|\d+[.)]|#{1,6}\s)")


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(ANSWER) or "").strip()
    if not text:
        return False
    if text.endswith("...") or text.endswith("…"):
        return True
    if any(marker in text.lower() for marker in MARKERS):
        return True
    if "```" in text:
        return False                              # 코드블록의 짝은 format_broken 이 본다
    last = text.splitlines()[-1]
    if _STRUCTURED.match(last):
        return False                              # 표·목록의 마지막 줄
    return not text.endswith(CLOSERS)
