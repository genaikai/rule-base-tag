"""답변에 실린 링크가 성립하지 않는가.

**연결되는지는 보지 않는다.** 이 프로그램은 밖으로 나가지 않으므로 확인할 수 있는
것은 꼴뿐이다 — 없는 스킴, 점 없는 호스트, 안 닫힌 괄호.
"""

import re

from ...schema import ANSWER
from .._shared import tally

NAME = "invalid_link"

_MD = re.compile(r"\[[^\]]*\]\(([^)]*)\)")      # [글](주소)
_BARE = re.compile(r"(?<!\()\bhttps?://\S+")
_SCHEME = re.compile(r"^(?:https?://|/|#)")


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(ANSWER) or "").strip()
    if not text:
        return False
    for url in _MD.findall(text):
        if not _valid(url.strip()):
            return True
    for url in _BARE.findall(text):
        if not _valid(url.rstrip(".,;:!?)")):
            return True
    return False


def _valid(url: str) -> bool:
    if not url or not _SCHEME.match(url):
        return False                              # htp:// · example.com · 빈 주소
    if url.startswith(("/", "#")):
        return True                               # 같은 문서 안이면 호스트가 없다
    host = url.split("://", 1)[1].split("/")[0]
    return "." in host and not host.startswith(".") and not host.endswith(".")
