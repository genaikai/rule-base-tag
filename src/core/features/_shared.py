"""기능 여럿이 같이 쓰는 것. 기능이 아니므로 이름 앞에 밑줄을 둔다.

둘 이상이 **같은 기준**을 써야 할 때만 여기로 올린다. 한 기능만 쓰는 것은 그 기능
폴더 안에 둔다 — 여기 올려두면 고칠 때 누가 영향받는지 알 수 없다.
"""

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


# 코드블록 안의 파이프는 셸 파이프고 괄호는 정규식 문법이지 마크다운 구조가 아니다.
# 그런데 글자만 보면 구별이 안 되므로, 마크다운을 보는 판정은 먼저 여기를 걷어낸다.
_FENCED = re.compile(r"^\s*```.*$")
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def prose_of(text: str) -> str:
    """코드블록·인라인 코드를 지운 나머지. 마크다운 구조를 보는 판정이 쓴다.

    지우되 **줄은 남긴다** — 표·헤딩 검사가 줄 단위로 돌아야 하는데, 줄이 사라지면
    표의 열 수를 셀 때 코드블록 건너편 줄이 붙어 한 표로 보인다.

    펜스가 안 닫힌 경우는 여는 줄부터 끝까지 코드로 본다. 어디까지가 코드인지
    정할 수 없는 상태라 어느 쪽으로 정해도 틀리는데, 이쪽이 오탐을 안 만든다 —
    그리고 안 닫힌 펜스 자체는 format_broken 이 갈라내기 전에 이미 본다.
    """
    out: list[str] = []
    in_code = False
    for line in text.splitlines():
        if _FENCED.match(line):
            in_code = not in_code
            out.append("")
            continue
        out.append("" if in_code else _INLINE_CODE.sub("", line))
    return "\n".join(out)


# 그 컬럼이 로그에 아직 없을 때 화면에 뜨는 값. `0 / 1,000` 은 "봤는데 없었다" 고
# 이것은 "보지 못했다" 다 — 둘을 같은 꼴로 찍으면 규칙이 죽은 것을 알 수 없다.
ABSENT = "n/a (컬럼 없음)"


def column_missing(rows: list[dict], name: str) -> bool:
    """이 컬럼이 로그에 아예 없는가. 있으면서 빈 것과는 다른 상태다."""
    return bool(rows) and name not in rows[0]


def tally(hits: int, total: int) -> str:
    """리포트에 한 줄로 들어갈 꼴. 비율은 보는 사람이 나눈다 —
    옮겨 적을 것이 적을수록 좋고, 두 숫자면 원본이 남는다."""
    return f"{hits:,} / {total:,}"
