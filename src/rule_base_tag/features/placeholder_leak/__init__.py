"""채워지지 않은 자리가 그대로 나갔는가.

`{{이름}}` · `[여기에 요약 삽입]` · `<INSERT_POLICY>` 처럼 **템플릿의 빈칸이 값으로
바뀌지 못한 채** 사용자에게 도착한 경우다.

format_broken 과 가르는 이유: 이건 포맷이 깨진 것이 아니라 **답변이 미완성**인 것이다.
마크다운으로는 멀쩡히 렌더되고, 원인도 다르다 — 렌더링 사고가 아니라 값 주입 실패다.
한 숫자에 섞으면 그 숫자를 보고 어디를 고쳐야 할지 알 수 없다.

`answer_truncated` 와도 다르다. 저쪽은 답변이 **중간에 끊긴** 것이고, 이쪽은 끝까지
왔는데 빈칸이 남은 것이다.

**대괄호가 위험하다.** `[1]` 각주 · `- [ ]` 체크박스 · `[글](주소)` 링크가 전부
대괄호를 쓴다. 그래서 괄호 자체가 아니라 **안쪽 내용**을 보고 가른다.
"""

import re

from ...schema import ANSWER
from .._shared import prose_of, tally

NAME = "placeholder_leak"

# Jinja·Handlebars·Mustache 계열. 이중 중괄호는 산문에 우연히 나오지 않는다.
# 홑중괄호는 넣지 않는다 — JSON 과 코드가 전부 걸린다.
_MUSTACHE = re.compile(r"\{\{[^{}]+\}\}")

# 대문자 토큰. 세 글자 이상만 본다 — `[OK]` `[Y/N]` 같은 짧은 약어는 정상 답변에
# 나오고, 두 글자짜리 플레이스홀더는 거의 없다.
_UPPER_TOKEN = r"[A-Z][A-Z0-9_ ]{2,}"
_ANGLE = re.compile(rf"<{_UPPER_TOKEN}>")          # <INSERT_POLICY>. 소문자 태그는 HTML
_BRACKET_UPPER = re.compile(rf"\[{_UPPER_TOKEN}\](?!\()")   # 뒤에 `(` 면 링크다

# 사람이 나중에 채우라고 남긴 한글 지시문. 대문자 규칙으로는 안 잡힌다.
_DIRECTIVE_WORDS = ("삽입", "입력", "기재", "작성", "추가", "여기에", "채워")
_BRACKET_KO = re.compile(r"\[([^\[\]]+)\](?!\()")

_PATTERNS = (_MUSTACHE, _ANGLE, _BRACKET_UPPER)


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(ANSWER) or "").strip()
    if not text:
        return False
    # 코드블록 안의 `{{ user.name }}` 은 템플릿 문법을 설명하는 정상 답변이다.
    prose = prose_of(text)
    if any(pat.search(prose) for pat in _PATTERNS):
        return True
    return any(any(word in inner for word in _DIRECTIVE_WORDS)
               for inner in _BRACKET_KO.findall(prose))
