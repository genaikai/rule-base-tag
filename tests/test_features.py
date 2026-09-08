"""판정별 오탐·미탐 케이스.

`--dry-run` 두 모드는 유형당 한 개씩만 보장한다 — 규칙이 살아있는지는 보지만,
규칙이 **정상 답변까지 켜는지**는 보지 못한다. 오탐은 여기서 지킨다.

케이스를 지울 때는 왜 지우는지 적어라. 여기 있는 것은 전부 한 번은 실제로
틀렸던 것들이다.
"""

import pytest

from rule_base_tag.features import (
    _shared,
    answer_truncated,
    format_broken,
    placeholder_leak,
)


# ── prose_of ────────────────────────────────────────────────────────────────
# 오탐의 상당수가 "코드블록 안의 내용에 마크다운 규칙을 적용해서" 생긴다.
# 코드 안의 파이프는 셸 파이프고 괄호는 정규식 문법이지 마크다운 구조가 아니다.

PROSE_CASES = [
    ("펜스 블록을 걷어낸다",
     "설명입니다.\n```bash\ncat a.txt | grep x\n```\n끝입니다.",
     ["설명입니다.", "끝입니다."],
     ["cat a.txt", "grep x"]),
    ("언어 태그가 붙은 펜스도 걷어낸다",
     "예시:\n```python\nre.compile(r'[^)]')\n```",
     ["예시:"],
     ["re.compile", "[^)]"]),
    ("인라인 코드를 걷어낸다",
     "쉘에서는 `ls | wc` 처럼 씁니다.",
     ["쉘에서는", "처럼 씁니다."],
     ["ls | wc"]),
    ("코드가 없으면 그대로 남는다",
     "영업일 기준 2~3일 걸립니다.",
     ["영업일 기준 2~3일 걸립니다."],
     []),
    ("펜스가 안 닫혔으면 여는 줄부터 끝까지 코드로 본다",
     "설명입니다.\n```python\nprint(1)",
     ["설명입니다."],
     ["print(1)"]),
]


@pytest.mark.parametrize("label,text,kept,dropped",
                         PROSE_CASES, ids=[c[0] for c in PROSE_CASES])
def test_prose_of_strips_code_regions(label, text, kept, dropped):
    prose = _shared.prose_of(text)
    for fragment in kept:
        assert fragment in prose, f"{label}: 산문 '{fragment}' 가 사라졌다"
    for fragment in dropped:
        assert fragment not in prose, f"{label}: 코드 '{fragment}' 가 남았다"


def test_prose_of_preserves_line_structure():
    """줄 수가 보존돼야 표·헤딩 검사가 줄 단위로 돌 수 있다."""
    text = "머리말\n```\ncode\n```\n꼬리말"
    assert len(_shared.prose_of(text).splitlines()) == len(text.splitlines())


# ── format_broken ───────────────────────────────────────────────────────────
# 이 표의 왼쪽 절반(오탐)이 이 판정의 존재 이유다. 느슨한 규칙이 만든 큰 숫자는
# 결과처럼 보이고, 사람은 그 숫자를 그대로 옮겨 적는다.

FORMAT_OK = [
    ("번호목록 1) 2)",      "환불 방법입니다.\n1) 주문 상세로 이동\n2) 환불 신청"),
    ("스마일 :)",           "네, 처리해 드렸습니다 :)"),
    ("(주) 표기",           "(주)한국물산으로 발송됩니다."),
    ("표 두 개",            "| a | b |\n|---|---|\n| 1 | 2 |\n\n다음 표입니다.\n\n"
                           "| x | y | z |\n|---|---|---|\n| 1 | 2 | 3 |"),
    ("표 뒤 산문에 파이프",   "| a | b |\n|---|---|\n| 1 | 2 |\n\n쉘에서는 `ls | wc` 처럼 씁니다."),
    ("코드블록 속 파이프",    "```bash\ncat a.txt | grep x\ngrep y\n```"),
    ("코드블록 속 정규식",    "```python\nre.compile(r'[^)]')\n```"),
    ("이모티콘",            "¯\\_(ツ)_/¯ 잘 모르겠습니다."),
    ("정상 표",             "| 항목 | 값 |\n|---|---|\n| a | 1 |"),
    ("정렬 지정 구분줄",      "| 항목 | 값 |\n|:---|---:|\n| a | 1 |"),
    ("일반 문장",           "영업일 기준 2~3일 걸립니다."),
    ("정상 링크",           "안내는 [환불 정책](https://ex.com/refund) 에 있습니다."),
    ("정상 헤딩",           "## 환불 절차\n\n주문 상세에서 신청합니다."),
    ("정상 굵게",           "**중요**: 환불은 **7일** 이내입니다."),
    ("산문 속 파이프 한 줄",  "환불 | 교환 둘 다 가능합니다."),
    ("체크박스 목록",        "- [ ] 주문 확인\n- [x] 환불 신청"),
    ("이스케이프한 파이프",   "| 항목 | 값 |\n|---|---|\n| a \\| b | 1 |"),
    ("JSON 답변 (L3 밖)",   '{"days": 7, "fee": 0}'),
]

FORMAT_BROKEN = [
    ("코드블록 안 닫힘",      "```python\nprint(1)"),
    ("구분줄 없는 표",        "| 항목 | 값 |\n| a | 1 |"),
    ("헤더·구분줄 열수 불일치", "| a | b | c |\n|---|---|\n| 1 | 2 | 3 |"),
    ("데이터 행 열수 불일치",   "| a | b |\n|---|---|\n| 1 | 2 | 3 |"),
    ("** 안 닫힘",           "**중요: 환불은 7일 이내입니다."),
    ("백틱 홀수",            "`code 를 실행하세요."),
    ("취소선 홀수",           "~~취소 환불은 7일 이내입니다."),
    ("헤딩 뒤 공백 없음",      "#환불 절차\n내용입니다."),
    ("헤딩 7단계",           "####### 환불 절차\n내용입니다."),
    ("리터럴 \\n 누출",       "1. 첫째\\n2. 둘째\\n3. 셋째"),
    ("대체문자 U+FFFD",      "환불 �� 절차입니다."),
    ("제어문자 혼입",         "환불 절차\x00입니다."),
    ("링크 괄호 안 닫힘",      "안내는 [환불 정책](https://ex.com/refund 에 있습니다."),
    ("링크 대괄호 안 닫힘",    "안내는 [환불 정책(https://ex.com/refund) 에 있습니다."),
]


@pytest.mark.parametrize("label,answer", FORMAT_OK, ids=[c[0] for c in FORMAT_OK])
def test_format_broken_does_not_fire_on_valid_answers(label, answer):
    assert format_broken._hit({"answer": answer}) is False, f"오탐: {label}"


@pytest.mark.parametrize("label,answer", FORMAT_BROKEN, ids=[c[0] for c in FORMAT_BROKEN])
def test_format_broken_fires_on_broken_answers(label, answer):
    assert format_broken._hit({"answer": answer}) is True, f"미탐: {label}"


def test_format_broken_ignores_empty_answer():
    """빈 답변은 model_thinking_stopped 의 몫이다. 둘 다 켜지면 어느 쪽인지 모른다."""
    assert format_broken._hit({"answer": ""}) is False
    assert format_broken._hit({"answer": None}) is False


# ── placeholder_leak ────────────────────────────────────────────────────────
# 채워지지 않은 자리가 그대로 나갔는가. "포맷이 깨졌다" 가 아니라 "답변이 미완성이다"
# 라서 format_broken 과 가른다 — 섞으면 그 숫자가 무슨 뜻인지 흐려진다.
#
# 대괄호가 위험하다. `[1]` 각주 · `- [ ]` 체크박스 · `[글](주소)` 링크가 전부
# 대괄호를 쓴다. 그래서 안쪽 내용을 보고 가른다.

LEAK_OK = [
    ("정상 문장",          "안녕하세요 홍길동님, 환불 안내입니다."),
    ("마크다운 링크",       "안내는 [환불 정책](https://ex.com/refund) 에 있습니다."),
    ("체크박스 목록",       "- [ ] 주문 확인\n- [x] 환불 신청"),
    ("각주 번호",          "환불은 7일 이내입니다 [1]."),
    ("소문자 HTML",        "<div class='box'>환불 안내</div>"),
    ("코드블록 속 템플릿",   "템플릿 예시입니다.\n```jinja\n{{ user.name }}\n```"),
    ("코드블록 속 대문자",   "```bash\nexport API_KEY=<YOUR_KEY>\n```"),
    ("정상 표",            "| 항목 | 값 |\n|---|---|\n| 기간 | 7일 |"),
    ("짧은 대문자 약어",     "결제는 [OK] 상태입니다."),
]

LEAK_BROKEN = [
    ("{{영문 변수}}",       "안녕하세요 {{user_name}}님, 주문 {{order_id}} 건입니다."),
    ("{{한글 변수}}",       "안녕하세요 {{이름}}님, 환불 안내입니다."),
    ("[한글 지시문]",       "환불 절차는 다음과 같습니다. [여기에 요약 삽입]"),
    ("<대문자 토큰>",       "환불은 <INSERT_POLICY> 기준으로 처리됩니다."),
    ("[대문자 토큰]",       "주문 [ORDER_ID] 건의 환불입니다."),
    ("[TODO] 잔존",        "[TODO] 환불 정책 확인 필요"),
]


@pytest.mark.parametrize("label,answer", LEAK_OK, ids=[c[0] for c in LEAK_OK])
def test_placeholder_leak_does_not_fire_on_valid_answers(label, answer):
    assert placeholder_leak._hit({"answer": answer}) is False, f"오탐: {label}"


@pytest.mark.parametrize("label,answer", LEAK_BROKEN, ids=[c[0] for c in LEAK_BROKEN])
def test_placeholder_leak_fires_on_leaked_answers(label, answer):
    assert placeholder_leak._hit({"answer": answer}) is True, f"미탐: {label}"


def test_placeholder_leak_ignores_empty_answer():
    assert placeholder_leak._hit({"answer": ""}) is False


# ── answer_truncated ────────────────────────────────────────────────────────

TRUNCATED_OK = [
    ("JSON 으로 끝남",     '{"days": 7, "fee": 0}'),
    ("HTML 태그로 닫힘",    "<div class='box'>환불은 7일 이내입니다.</div>"),
    ("마침표로 끝남",       "영업일 기준 2~3일 걸립니다."),
    ("한글 종결어미",       "주문 상세 화면에서 신청하실 수 있습니다"),
]


@pytest.mark.parametrize("label,answer", TRUNCATED_OK, ids=[c[0] for c in TRUNCATED_OK])
def test_answer_truncated_does_not_fire_on_complete_answers(label, answer):
    """`}` 가 CLOSERS 에 없어서 유효한 JSON 이 100% 잘림으로 세어지던 것을 막는다.

    `</div>` 로 **제대로 닫은** HTML 이 벌을 받는 것도 같은 원인이었다.
    """
    assert answer_truncated._hit({"answer": answer}) is False, f"오탐: {label}"


def test_answer_truncated_still_catches_real_truncation():
    assert answer_truncated._hit({"answer": "환불 절차는 다음과 같습니"}) is True
    assert answer_truncated._hit({"answer": "환불 절차는..."}) is True


# ── 합성 데이터가 판정 전부를 실제로 훑는가 ─────────────────────────────────
# README 가 보증한다고 적은 것을 그대로 검사한다. 판정을 추가하면서 synth.py 의
# `_DEFECTS` 에 넣는 것을 잊으면, 그 규칙은 한 번도 켜지지 않고 화면에는 `0` 으로
# 뜬다 — 그리고 `0` 은 "문제 없음" 과 구별되지 않는다.


def _metrics(mode: str) -> dict:
    from rule_base_tag.pipeline import process_data
    from rule_base_tag.synth import generate
    return process_data(generate(300, seed=0, mode=mode))


def test_clean_data_trips_no_feature():
    dead = {k: v for k, v in _metrics("normal").items()
            if k != "rows" and not v.startswith("0 /")}
    assert not dead, f"깨끗한 데이터에서 켜졌다 (오탐): {dead}"


def test_adversarial_data_trips_every_feature():
    from rule_base_tag.pipeline import FEATURES
    metrics = _metrics("adversarial")
    dead = [f.NAME for f in FEATURES if metrics[f.NAME].startswith("0 /")]
    assert not dead, f"합성 데이터가 이 판정을 한 번도 켜지 않았다: {dead}"
