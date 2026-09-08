"""스키마에서 파생된 합성 데이터 생성기.

가짜 데이터는 **파일이 아니라 코드로** 존재한다. 저장소에 데이터 파일이 없으면
실수로 커밋될 파일 자체가 없다.
테스트도 픽스처 파일 대신 이 함수를 호출한다.

두 모드가 서로 다른 것을 보증한다.

    normal        어떤 판정에도 걸리지 않는 깨끗한 데이터.
                  전 구간이 도는지, 그리고 판정이 헛돌지 않는지를 본다
    adversarial   판정마다 그 유형을 하나씩 심는다.
                  실행하면 전부 켜져야 한다 — 하나라도 0 이면 그 규칙이 죽은 것이다

깨끗한 쪽 표본에는 판정에 걸릴 것을 넣지 않는다. 한글 표본에 로마자를 섞으면
language_mixing 이 켜지고, 마침표 세 개를 쓰면 answer_truncated 가 켜진다.
표본을 고칠 때 이 점을 먼저 본다.
"""

import random
from datetime import datetime, timedelta

from .schema import ANSWER, INPUT_SCHEMA, QUERY

# 질문·답변은 언어를 맞춰 짝으로 뽑는다. 따로 뽑으면 language_mismatch 가
# 깨끗한 쪽에서 켜진다.
_SAMPLES = {
    "ko": (
        ("환불 절차를 알려줘", "주문 상세 화면에서 환불을 신청하실 수 있습니다."),
        ("배송이 얼마나 걸리나요", "영업일 기준 이틀에서 사흘 정도 걸립니다."),
        ("비밀번호를 바꾸고 싶어요", "설정 화면의 계정 항목에서 변경하실 수 있습니다."),
    ),
    "en": (
        ("How do I request a refund?",
         "You can request a refund from the order details page."),
        ("When will my order arrive?",
         "Standard delivery takes two to three business days."),
        ("Can I change my delivery address?",
         "Yes, you can update it before the order ships."),
    ),
}


# 판정이 읽지 않는 컬럼들. 값은 **꼴만 맞다** — 실제 로그의 값·분포를 흉내내지
# 않는다. 여기 있는 것은 "스키마를 통과하는가" 를 보는 용도뿐이고, 판정을 흔들지
# 않아야 한다. 사람 이름·부서명 자리에 그럴듯한 값을 넣으면 sensitive_info 가
# 자기 표본이 아닌 곳에서 켜질 수 있다.
_EPOCH = datetime(2026, 1, 5, 9, 0, 0)


def _context_columns(rng: random.Random) -> dict:
    """판정이 안 읽는 컬럼 34개. 스키마를 만족하는 최소한의 꼴로 채운다."""
    n = rng.randrange(1, 1000)
    start = _EPOCH + timedelta(minutes=rng.randrange(0, 60 * 24 * 5),
                               microseconds=rng.randrange(0, 1_000_000))
    end = start + timedelta(seconds=rng.uniform(0.5, 30.0))
    # 피드백은 대부분의 턴에 없다. 빈 값이 널로 읽히는지도 여기서 같이 돈다
    scored = rng.random() < 0.1
    return {
        "log_table": "chat_log",
        "db_dept_name": f"dept-{n:03d}",
        "db_position_name": f"position-{n % 7}",
        "db_id": f"db-{n:05d}",
        "db_route_result": "routed",
        "assist_name": "assistant-a",
        "model_name": "model-a",
        "dept_div_name": f"div-{n % 5}",
        "div_name": f"div-{n % 5}",
        "dept_name": f"dept-{n:03d}",
        "user_name": f"user-{n:05d}",
        "user_id": f"u{n:05d}",
        "user_type": "internal",
        "job_grade": f"grade-{n % 9}",
        "job": f"job-{n % 11}",
        "chat_id": f"chat-{n:06d}",
        "input_msg_id": f"msg-{n:08d}",
        "turn_start_week": f"{start:%G-W%V}",
        "turn_start_weekday": f"{start:%a}",
        "turn_start_date": f"{start:%Y-%m-%d %H:%M:%S}",
        "input_msg_start_time": f"{start:%Y-%m-%d %H:%M:%S.%f}",
        "output_msg_end_time": f"{end:%Y-%m-%d %H:%M:%S.%f}",
        "prompt_template_name": "template-a",
        "rag_yn": "true" if n % 2 else "false",
        "rag_decide_yn": "true" if n % 3 else "false",
        "input_msg_type": "text",
        "input_msg_sub_type": "text",
        "output_msg_type": "text",
        "output_msg_sub_type": "text",
        "feedback_type": "thumbs" if scored else "",
        "feedback_score": str(rng.randrange(0, 6)) if scored else "",
        "feedback_category": "",
        "feedback_content": "",
        "feedback_detail_content": "",
    }


def _clean_row(rng: random.Random) -> dict:
    """어떤 판정에도 걸리지 않는 한 행."""
    lang = rng.choice(list(_SAMPLES))
    query, answer = rng.choice(_SAMPLES[lang])
    return {**_context_columns(rng), QUERY: query, ANSWER: answer}


# ── 판정 유형별 사고 주입 ──────────────────────────────────────────────────
# 판정 하나에 함수 하나. 판정을 추가하면 여기에도 하나 추가한다 — 안 그러면
# 그 규칙은 합성 데이터에서 한 번도 켜지지 않고, 죽었는지 알 수 없다.

# 심는 유형끼리 서로 켜지 않게 언어를 맞춰 통째로 덮어쓴다. 한글 답변에 영문
# 링크를 덧붙이는 식으로 만들면 language_mixing 까지 같이 켜져서, 어느 규칙이
# 무엇을 잡은 것인지 숫자만 보고는 알 수 없게 된다.
_EN_Q = "How do I request a refund?"

def _d_error_keyword(row: dict) -> None:
    row[QUERY] = _EN_Q
    row[ANSWER] = "The lookup failed on our side."


def _d_answer_truncated(row: dict) -> None:
    row[ANSWER] = row[ANSWER][:18] + "..."            # 언어는 그대로 둔다


def _d_language_mixing(row: dict) -> None:
    row[QUERY] = "환불 절차를 알려줘"
    row[ANSWER] = "환불은 order details 화면에서 신청하세요."


def _d_format_broken(row: dict) -> None:
    # 줄마다 파이프 개수가 다르다. 글자를 안 넣어 다른 판정을 건드리지 않는다
    row[ANSWER] = "| 1 | 2 |\n| 3 |"


def _d_sensitive_info(row: dict) -> None:
    row[QUERY] = _EN_Q
    row[ANSWER] = "You can reach us at hong@example.com for the details."


def _d_language_mismatch(row: dict) -> None:
    row[QUERY] = "환불 절차를 알려줘"
    row[ANSWER] = "You can request a refund from the order details page."


def _d_invalid_link(row: dict) -> None:
    row[QUERY] = _EN_Q
    row[ANSWER] = "See the guide at [manual](htp://example) for the details."


def _d_model_thinking_stopped(row: dict) -> None:
    row[ANSWER] = ""                                  # 답변을 받지 못했다


def _d_placeholder_leak(row: dict) -> None:
    # 플레이스홀더를 순한글로 둔다. 로마자를 쓰면 language_mixing 까지 같이 켜져서
    # 어느 규칙이 무엇을 잡은 것인지 숫자만 보고는 알 수 없다.
    row[QUERY] = "환불 절차를 알려줘"
    row[ANSWER] = "안녕하세요 {{이름}}님, 환불은 영업일 기준 사흘 걸립니다."


# empty_retrieved_docs · empty_search_query 는 여기 없다 — 읽을 컬럼이 로그에
# 아직 없어서 심을 자리가 없다. 그 둘은 화면에 n/a 로 뜨고, 규칙이 살아 있는지는
# tests/test_features.py 의 단위 케이스가 지킨다.
_DEFECTS = (
    _d_error_keyword,
    _d_answer_truncated,
    _d_language_mixing,
    _d_format_broken,
    _d_sensitive_info,
    _d_language_mismatch,
    _d_invalid_link,
    _d_model_thinking_stopped,
    _d_placeholder_leak,
)


def _break_schema(row: dict) -> None:
    """스키마 자체를 깨뜨린다. 판정이 아니라 `schema` 줄에 뜨는 쪽이다."""
    row[QUERY] = ""                                   # nullable=False 인데 빈 값


def generate(n: int = 1000, seed: int = 0, mode: str = "normal") -> list[dict]:
    """스키마를 읽어 합성 데이터를 만든다. 같은 seed 는 같은 데이터를 준다.

    mode="normal"      어떤 판정에도 걸리지 않는 데이터
    mode="adversarial" 판정 유형을 하나씩 돌아가며 심고, 스키마 위반도 섞는다
    """
    rng = random.Random(seed)
    rows: list[dict] = []
    for i in range(n):
        row = _clean_row(rng)
        if mode == "adversarial":
            # 돌아가며 심어서 n 이 작아도 모든 유형이 나오게 한다.
            # 확률로 고르면 seed 에 따라 어떤 유형은 한 번도 안 나온다.
            if i % 3 == 0:
                _DEFECTS[(i // 3) % len(_DEFECTS)](row)
            if i % 97 == 0:
                _break_schema(row)
        rows.append(row)
    return rows


# 스키마에 필드를 더했는데 표본을 안 고치면 그 필드가 통째로 빠진 행이 나온다.
# 조용히 빠지면 `schema` 줄에 "column missing" 으로만 떠서 원인을 찾기 어렵다.
assert {f.name for f in INPUT_SCHEMA} == set(_clean_row(random.Random(0))), (
    "INPUT_SCHEMA 와 합성 표본의 필드가 다르다 — synth.py 의 _clean_row 를 맞춰라"
)
