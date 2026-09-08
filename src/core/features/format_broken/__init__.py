"""표·코드블록·강조 같은 구조가 깨졌는가.

**판정 기준을 손대기 전에 옆의 `RULES.md` 를 읽어라.** 무엇을 일부러 안 보는지와
그 이유가 거기 있다 — 모르고 넓히면 오탐이 돌아온다.

세 층위를 본다.

    L1 블록 구조   펜스 짝 · 표 · 헤딩          markdown.py
    L2 인라인      `**` `` ` `` `~~` · 링크 문법   markdown.py
    L4 문자 손상   리터럴 \\n · 대체문자 · 제어문자  corruption.py

**JSON·HTML·LaTeX 는 보지 않는다 (L3).** 그건 "답변이 그 포맷이어야 한다"는 전제가
있어야 성립하는데, 지금 그 전제를 확인할 방법이 없다 — `schema.py` 의 컬럼 이름조차
실제 로그로 확인한 것이 아니다. README 의 "아직 안 된 것" 에 구멍으로 적어 두었다.

**채워지지 않은 플레이스홀더는 placeholder_leak 이 본다.** 그건 포맷이 깨진 것이
아니라 답변이 미완성인 것이라, 같은 숫자에 섞으면 그 숫자가 무슨 뜻인지 흐려진다.
"""

from ...schema import ANSWER
from .._shared import prose_of, tally
from . import corruption, markdown

NAME = "format_broken"

_FENCE = "```"


def process_data(rows: list[dict]) -> dict:
    hits = sum(1 for row in rows if _hit(row))
    return {NAME: tally(hits, len(rows))}


def _hit(row: dict) -> bool:
    text = (row.get(ANSWER) or "").strip()
    if not text:
        return False                              # 빈 답변은 model_thinking_stopped
    # 펜스 짝을 제일 먼저 본다. 안 맞으면 어디까지가 코드인지 정할 수 없고,
    # 틀린 경계 위에서 나온 마크다운 판정은 믿을 수 없다.
    if text.count(_FENCE) % 2:
        return True
    if corruption.hit(text):
        return True
    return markdown.hit(prose_of(text))
