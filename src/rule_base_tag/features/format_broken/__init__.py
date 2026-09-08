"""표·코드블록·괄호 같은 구조가 깨졌는가."""

from ...schema import ANSWER
from .._shared import tally

NAME = "format_broken"

PAIRS = {"[": "]", "{": "}", "(": ")"}


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(ANSWER) or "").strip()
    if not text:
        return False
    if text.count("```") % 2:                      # 코드블록이 안 닫혔다
        return True
    if "|" in text and _ragged_table(text):
        return True
    return _unbalanced(text)


def _ragged_table(text: str) -> bool:
    """표의 줄마다 칸 수가 다르면 깨진 것으로 본다."""
    counts = [line.count("|") for line in text.splitlines() if "|" in line]
    return len(set(counts)) > 1


def _unbalanced(text: str) -> bool:
    stack: list[str] = []
    for char in text:
        if char in PAIRS:
            stack.append(char)
        elif char in PAIRS.values():
            if not stack or PAIRS[stack.pop()] != char:
                return True
    return bool(stack)
