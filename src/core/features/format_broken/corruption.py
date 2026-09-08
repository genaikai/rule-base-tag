"""마크다운 이전의 손상. 답변 **전체**를 본다.

여기 것들은 마크다운이 맞고 틀리고를 떠나 텍스트 자체가 상한 경우다. 그래서
`prose_of()` 를 통과시키지 않는다 — 코드블록 안에서 상해도 상한 것이다.
"""

import re

_REPLACEMENT = "�"                            # 인코딩이 어긋날 때 남는 자리
# C0 제어문자 중 탭·개행·복귀만 뺀다. 나머지가 본문에 있으면 정상이 아니다.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_ESCAPE = re.compile(r"\\[nt]")


def hit(text: str) -> bool:
    if _REPLACEMENT in text or _CONTROL.search(text):
        return True
    return _escape_leaked(text)


def _escape_leaked(text: str) -> bool:
    """`\\n` 이 개행이 되지 못하고 글자로 찍혔는가.

    파이프라인 어딘가에서 이스케이프가 한 번 덜 풀리면 답변이 통째로 한 줄이 된다.
    화면으로는 멀쩡해 보이므로 사람 눈으로는 잘 안 걸린다.

    실제 개행이 하나도 없을 것을 조건으로 단다. 개행이 있는데 `\\n` 도 있으면
    그건 코드나 정규식을 설명하는 정상 답변일 가능성이 높다.
    """
    return "\n" not in text and len(_ESCAPE.findall(text)) >= 2
