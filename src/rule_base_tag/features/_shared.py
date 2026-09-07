"""판정 여럿이 같이 쓰는 것. 기능이 아니므로 이름 앞에 밑줄을 둔다."""

import re

# 문자 체계별 대표 구간. 언어를 가리는 판정 둘이 같은 기준을 써야 해서 여기 둔다 —
# 따로 두면 한쪽만 고쳐지고, 그러면 두 판정이 서로 다른 언어를 보게 된다.
SCRIPTS = {
    "hangul": re.compile(r"[가-힣]"),
    "latin": re.compile(r"[A-Za-z]"),
    "cjk": re.compile(r"[一-鿿぀-ヿ]"),
    "cyrillic": re.compile(r"[Ѐ-ӿ]"),
    "arabic": re.compile(r"[؀-ۿ]"),
}


def scripts_in(text: str) -> set:
    """이 글에 나타나는 문자 체계들."""
    return {name for name, pat in SCRIPTS.items() if pat.search(text)}


def dominant_script(text: str):
    """가장 많이 쓰인 문자 체계. 판정할 만큼 없으면 None."""
    counts = {name: len(pat.findall(text)) for name, pat in SCRIPTS.items()}
    best = max(counts, key=counts.get)
    # 글자다운 글자가 거의 없으면 (숫자·기호뿐이면) 언어를 말하지 않는다.
    return best if counts[best] >= 3 else None


def tally(hits: int, total: int) -> str:
    """리포트에 한 줄로 들어갈 꼴. 비율은 보는 사람이 나눈다 —
    옮겨 적을 것이 적을수록 좋고, 두 숫자면 원본이 남는다."""
    return f"{hits:,} / {total:,}"
