"""마크다운 구조와 강조. **코드블록을 걷어낸 산문에만** 들이댄다.

코드 안의 파이프는 셸 파이프고 괄호는 정규식 문법이다 — 마크다운 구조가 아닌데
글자만 보면 구별이 안 된다. 그래서 부르는 쪽이 `prose_of()` 를 먼저 통과시킨다.
"""

import re

# 표의 구분줄. 이게 없으면 렌더러가 표로 안 그린다 — 파이프 개수가 고르더라도
# 결과물은 그냥 파이프가 든 문단이다.
_DELIMITER = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
# 셀 안의 `\|` 는 칸을 가르지 않는다. 세기 전에 지운다.
_ESCAPED_PIPE = re.compile(r"\\\|")

_HEADING_NO_SPACE = re.compile(r"^#{1,6}[^#\s]")   # `#환불` — 제목이 안 된다
_HEADING_TOO_DEEP = re.compile(r"^#{7,}")          # 마크다운은 6단계까지다

# 여는 기호와 닫는 기호가 같아서, 개수가 홀수면 짝이 없다는 뜻이다.
# `*` 단독은 넣지 않는다 — 목록 마커 `* 항목` 과 곱하기에서 구별이 안 된다.
_PAIRED = ("**", "`", "~~")

_LINK_OPEN = re.compile(r"\]\(")


def hit(prose: str) -> bool:
    return (_broken_table(prose)
            or _broken_heading(prose)
            or _unpaired_emphasis(prose)
            or _broken_link(prose))


def _broken_table(prose: str) -> bool:
    """표 블록마다 따로 본다.

    이전 판은 `|` 가 든 **모든 줄**을 한 표로 셌다. 그래서 표를 두 개 쓴 답변은
    열 수가 달라 무조건 깨진 것이 됐고, 표를 잘 쓴 답변일수록 걸렸다.
    """
    for block in _table_blocks(prose.splitlines()):
        if len(block) < 2:
            continue                              # 한 줄짜리는 표인지 알 수 없다
        widths = {_ESCAPED_PIPE.sub("", line).count("|") for line in block}
        if len(widths) > 1:
            return True                           # 줄마다 칸 수가 다르다
        if not _DELIMITER.match(block[1]):
            return True                           # 구분줄이 없다
    return False


def _table_blocks(lines: list[str]) -> list[list[str]]:
    """파이프가 든 줄이 연속으로 이어지는 구간들."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if "|" in line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _broken_heading(prose: str) -> bool:
    return any(_HEADING_NO_SPACE.match(line) or _HEADING_TOO_DEEP.match(line)
               for line in prose.splitlines())


def _unpaired_emphasis(prose: str) -> bool:
    """`**` · `` ` `` · `~~` 가 홀수면 기호가 글자로 노출된다."""
    return any(prose.count(mark) % 2 for mark in _PAIRED)


def _broken_link(prose: str) -> bool:
    """링크 문법이 성립하는가. 주소가 유효한지는 invalid_link 의 몫이다.

    `invalid_link` 의 정규식은 `[글](주소)` 가 **온전할 때만** 매칭되므로, 문법이
    깨진 링크는 그쪽 그물을 통과한다. 그 구멍을 여기서 막는다.

    괄호 `()` 와 중괄호 `{}` 는 세지 않는다 — `1)` 번호목록, `:)`, `(주)`, JSON 이
    전부 걸린다. 대괄호는 산문에서 거의 링크·각주 문법이라 셀 수 있다.
    """
    for line in prose.splitlines():
        for match in _LINK_OPEN.finditer(line):
            if ")" not in line[match.end():]:
                return True                       # 같은 줄에서 안 닫혔다
    return prose.count("[") != prose.count("]")
