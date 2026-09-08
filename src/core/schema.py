"""입력 데이터 스키마 — 입력 형식에 대해 아는 것의 유일한 출처다.

실제 데이터에서 확인한 형식은 여기에만 반영한다. 적는 것은 구조뿐이다:
이름 / 타입 / 널 허용 / 허용값 / 범위. 실제 값·분포·식별 가능한 코드값은 적지 않는다.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Field:
    name: str
    dtype: str                      # "int" | "float" | "str" | "datetime" | "category"
    nullable: bool
    allowed: tuple | None = None    # 카테고리 허용값
    rng: tuple | None = None        # (min, max)
    note: str = ""                  # 실제 데이터에서 확인된 사실을 적는 자리
    used: bool = True               # 처리 로직이 이 필드를 읽나


################################################################################
# Field 의 각 자리
#   name:     컬럼 이름
#   dtype:    "int" | "float" | "str" | "datetime" | "category"
#   nullable: False = 필수, True = 빈 값 허용
#   allowed:  category 일 때 허용값 튜플
#   rng:      (min, max) 범위 검사 (int/float)
#   note:     실제 로그에서 확인한 것 / 아직 확인 못 한 것
#   used:     False = 로그에는 있지만 판정이 읽지 않는다
################################################################################
# 컬럼 이름은 여기서만 정한다. 판정 로직은 이 상수를 import 해서 쓴다 —
# 로그의 컬럼 이름이 바뀌면 고칠 곳이 이 두 줄뿐이어야 한다.
QUERY = "input_msg_content"
ANSWER = "output_msg_content"

# 아직 로그에 없는 컬럼. 이것을 읽는 판정 둘(empty_search_query,
# empty_retrieved_docs)은 코드를 그대로 두고 화면에 n/a 로 뜬다.
# INPUT_SCHEMA 에 미리 넣어두면 매 실행 "column missing" 위반이 떠서 종료 코드가
# 1 로 굳고, 그러면 진짜 위반과 구별되지 않는다. 컬럼이 붙는 날 필드를 더한다.
SEARCH_QUERY = "search_query"
RETRIEVED_DOCS = "retrieved_docs"

INPUT_SCHEMA: tuple[Field, ...] = (
    # ── 판정이 읽는 둘 ────────────────────────────────────────────────────
    Field(QUERY, "str", False,
          note="사용자 입력 원문. 빈 값이 실제로 있는지 확인 필요"),
    # 답변을 못 받고 끝난 턴이 빈 값으로 들어오는지 행 자체가 없는지 아직 모른다.
    # 전자면 nullable=True 가 맞고, model_thinking_stopped 가 그 행을 잡는다.
    Field(ANSWER, "str", True,
          note="모델 답변 원문. 빈 값의 의미 확인 필요"),

    # ── 아래는 전부 used=False ────────────────────────────────────────────
    # 로그에는 있지만 어떤 판정도 읽지 않는다. 어긋나도 판정은 멀쩡하므로 위반이
    # 아니라 노트로 내려간다 — 매 실행마다 뜨는 줄이 있으면 사람은 곧 schema 줄
    # 자체를 안 보게 되고, 그러면 진짜 위반도 같이 안 보인다.
    # 판정이 이 중 하나를 읽기 시작하면 그 줄만 used=True 로 올린다.
    #
    # nullable 은 전부 True 로 시작한다. 근거 없이 조였다가 틀리면 매 실행 노트가
    # 뜨는데, 그건 이 컬럼들에 대해 아무것도 알려주지 않는다.

    # 출처·경로
    Field("log_table", "str", True, used=False, note="로그가 나온 테이블 이름"),
    Field("db_route_result", "str", True, used=False, note="라우팅 결과"),
    Field("assist_name", "str", True, used=False),
    Field("model_name", "str", True, used=False, note="답변을 만든 모델 이름"),
    Field("prompt_template_name", "str", True, used=False),

    # 사람·조직. 값 자체가 개인정보다 — 화면에도 스키마에도 실값을 적지 않는다
    Field("db_dept_name", "str", True, used=False),
    Field("db_position_name", "str", True, used=False),
    Field("db_id", "str", True, used=False),
    Field("dept_div_name", "str", True, used=False),
    Field("div_name", "str", True, used=False),
    Field("dept_name", "str", True, used=False),
    Field("user_name", "str", True, used=False),
    Field("user_id", "str", True, used=False),
    Field("user_type", "str", True, used=False,
          note="값의 가짓수가 적다면 category 로 올릴 자리"),
    Field("job_grade", "str", True, used=False),
    Field("job", "str", True, used=False),

    # 시각. fromisoformat 이 소수점 이하 유무를 둘 다 받으므로 포맷 문자열은 두지
    # 않는다 (turn_start_date 는 초까지, 나머지 둘은 마이크로초까지 온다)
    Field("chat_id", "str", True, used=False, note="대화 묶음. 한 행은 그 안의 한 턴"),
    Field("input_msg_id", "str", True, used=False),
    Field("turn_start_week", "str", True, used=False),
    Field("turn_start_weekday", "str", True, used=False),
    Field("turn_start_date", "datetime", True, used=False),
    Field("input_msg_start_time", "datetime", True, used=False),
    Field("output_msg_end_time", "datetime", True, used=False),

    # 검색 여부. 검색 질의도 문서 본문도 로그에 없고, 탔는지 여부만 있다
    Field("rag_yn", "category", True, used=False, allowed=("true", "false")),
    Field("rag_decide_yn", "category", True, used=False, allowed=("true", "false")),

    # 메시지 종류. 허용값을 아직 모른다 — 알게 되면 category 로 올린다
    Field("input_msg_type", "str", True, used=False),
    Field("input_msg_sub_type", "str", True, used=False),
    Field("output_msg_type", "str", True, used=False),
    Field("output_msg_sub_type", "str", True, used=False,
          note="답변이 끊긴 턴이 여기 찍히는지 확인 필요 — 그러면 판정이 읽는다"),

    # 피드백. 대부분의 행에는 없다
    Field("feedback_type", "str", True, used=False),
    Field("feedback_score", "int", True, used=False,
          note="0 부터 시작하는 정수. 상한 확인 필요라 rng 를 걸지 않았다"),
    Field("feedback_category", "str", True, used=False),
    Field("feedback_content", "str", True, used=False),
    Field("feedback_detail_content", "str", True, used=False),
)

NULL_TOKENS = frozenset({"", "NA", "N/A", "null", "NULL", "None", "-"})


def parse(value: str, dtype: str):
    """문자열을 dtype 으로 해석한다. 실패하면 ValueError."""
    if dtype == "int":
        return int(value)
    if dtype == "float":
        return float(value)
    if dtype == "datetime":
        return datetime.fromisoformat(value)
    return str(value)


def is_null(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() in NULL_TOKENS)


@dataclass(frozen=True)
class Report:
    """스키마 대조 결과. 위반과 노트를 가른다.

    위반(violations) 은 "판정이 틀렸을 수 있다"는 뜻이고, 노트(notes) 는 "어긋났지만
    처리 로직이 안 읽는다"는 뜻이다. 둘을 섞으면 매 실행마다 뜨는 줄이 생기고,
    사람은 곧 schema 줄 자체를 안 보게 된다 — 그러면 이 출력이 쓸모없어진다.
    """

    violations: list[str]
    notes: list[str]

    @property
    def ok(self) -> bool:
        return not self.violations


# 이름 자리의 폭. 가장 긴 컬럼 이름에 한 칸을 더한 값이다 — 좁으면 패딩이 아예
# 안 먹어서 줄마다 콜론 위치가 달라지고, 눈으로 훑을 때 그 줄을 놓친다.
LABEL = 24


def _field_messages(f: Field, rows: list[dict]) -> list[str]:
    """한 필드의 어긋남을 사람이 그대로 옮겨 적을 수 있는 한 줄씩으로."""
    nulls = bad_type = out_of_range = 0
    unexpected: set = set()

    for row in rows:
        raw = row.get(f.name)
        if is_null(raw):
            nulls += 1
            continue
        try:
            value = parse(raw, f.dtype)
        except (TypeError, ValueError):
            bad_type += 1
            continue
        if f.allowed is not None and value not in f.allowed:
            unexpected.add(value)
        if f.rng is not None and not (f.rng[0] <= value <= f.rng[1]):
            out_of_range += 1

    out: list[str] = []
    if nulls and not f.nullable:
        out.append(f"{f.name:<{LABEL}}: {nulls:,} nulls but nullable=False")
    if bad_type:
        out.append(f"{f.name:<{LABEL}}: dtype {f.dtype} expected, {bad_type:,} rows failed to parse")
    if unexpected:
        shown = sorted(unexpected)[:5]
        more = "" if len(unexpected) <= 5 else f" (+{len(unexpected) - 5} more)"
        out.append(f"{f.name:<{LABEL}}: unexpected values {set(shown)}{more}")
    if out_of_range:
        out.append(f"{f.name:<{LABEL}}: {out_of_range:,} rows outside {f.rng}")
    return out


def validate(rows: list[dict]) -> Report:
    """스키마를 대조한다.

    콘솔이 유일한 출력이라, 이 줄을 사람이 그대로 옮겨 적는 것이 전제다.
    따라서 "validation failed" 같은 요약 메시지는 결함이다 —
    옮겨 적을 것이 없기 때문이다.
    """
    if not rows:
        return Report([f"{'input':<{LABEL}}: 0 rows"], [])

    present = set(rows[0])
    violations: list[str] = []
    notes: list[str] = []

    for f in INPUT_SCHEMA:
        sink = violations if f.used else notes
        if f.name not in present:
            sink.append(f"{f.name:<{LABEL}}: column missing")
            continue
        sink.extend(_field_messages(f, rows))

    extra = present - {f.name for f in INPUT_SCHEMA}
    if extra:
        # 선언되지 않은 컬럼은 처리 로직이 읽을 리 없다 — 알려는 주되 위반은 아니다
        notes.append(f"{'(schema)':<{LABEL}}: undeclared columns {sorted(extra)}")
    return Report(violations, notes)
