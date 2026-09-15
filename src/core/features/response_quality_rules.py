"""
response_quality_rules.py

LLM 답변(output_msg_content)에 대한 rule-based 품질 검사 모듈.
LLM 호출 없이 정규식/유니코드 범위/휴리스틱만으로 판별한다.

사용 예:
    import pandas as pd
    from response_quality_rules import apply_flags

    df = pd.read_csv("data.csv")
    df = apply_flags(df)
    df.to_csv("data_flagged.csv", index=False)

각 검사 함수는 True/False를 반환하며, True인 케이스의 태그가
Flags 컬럼에 리스트로 쌓인다. 예: ['include_error_keyword', 'truncated_answer']
"""

from __future__ import annotations

import re
import unicodedata
from typing import Callable, Iterable, Optional

# ---------------------------------------------------------------------------
# 설정 상수 (필요에 맞게 직접 추가/수정하세요)
# ---------------------------------------------------------------------------

QUERY_HEAD_LEN = 100  # 질의는 앞에서부터 이만큼만 잘라서 사용

# 1. 정보 없음 관련 키워드 — 여기에 계속 추가하면 됨
NO_INFO_KEYWORDS: tuple[str, ...] = (
    "정보가 없",
    "제공되지 않아",
)

# ---------------------------------------------------------------------------
# 유니코드 범위 헬퍼
# ---------------------------------------------------------------------------

RE_HANGUL = re.compile(r"[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]")
RE_HAN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")   # 한자(중국어/일본어 공용)
RE_KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u31f0-\u31ff]")  # 히라가나/가타카나
RE_LATIN = re.compile(r"[A-Za-z\u00c0-\u024f\u1e00-\u1eff]")
RE_VIET_DIACRITIC = re.compile(
    r"[ăâđêôơưĂÂĐÊÔƠƯ]"
    r"|[\u1ea0-\u1ef9]"                       # 베트남어 전용 확장 라틴
    r"|[àáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệ]"
    r"|[ìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]",
    re.IGNORECASE,
)

# 코드블록/인라인코드 — 언어 판별·언어혼용 검사에서 제외
RE_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
RE_INLINE_CODE = re.compile(r"`[^`\n]+`")
RE_URL_ANY = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


def _strip_noise(text: str) -> str:
    """언어 판별 시 노이즈가 되는 코드/URL을 제거."""
    text = RE_CODE_BLOCK.sub(" ", text)
    text = RE_INLINE_CODE.sub(" ", text)
    text = RE_URL_ANY.sub(" ", text)
    return text


def _safe_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value != value:  # NaN
        return ""
    return str(value)


def detect_language(text: str) -> str:
    """
    문자 분포 기반 대표 언어 판별.
    반환값: 'ko' | 'ja' | 'zh' | 'vi' | 'en' | 'unknown'
    """
    text = _strip_noise(_safe_str(text))
    if not text.strip():
        return "unknown"

    n_hangul = len(RE_HANGUL.findall(text))
    n_kana = len(RE_KANA.findall(text))
    n_han = len(RE_HAN.findall(text))
    n_latin = len(RE_LATIN.findall(text))
    total = n_hangul + n_kana + n_han + n_latin
    if total == 0:
        return "unknown"

    # 가나가 유의미하게 있으면 일본어
    if n_kana >= 2 or (n_kana >= 1 and n_hangul == 0 and n_latin < 3):
        return "ja"
    # 한글이 가장 많으면 한국어
    if n_hangul / total >= 0.30:
        return "ko"
    # 한자 위주면 중국어
    if n_han / total >= 0.30:
        return "zh"
    # 라틴 계열 → 베트남어 vs 영어
    if n_latin / total >= 0.30:
        if RE_VIET_DIACRITIC.search(text):
            return "vi"
        return "en"
    if n_hangul > 0:
        return "ko"
    return "unknown"


# ---------------------------------------------------------------------------
# 1. 정보 없음 키워드 포함 여부
# ---------------------------------------------------------------------------

def has_no_info_keyword(
    answer: str,
    keywords: Iterable[str] = NO_INFO_KEYWORDS,
) -> bool:
    """답변에 '정보 없음' 계열 키워드가 포함되어 있으면 True."""
    answer = _safe_str(answer)
    if not answer:
        return False
    return any(kw in answer for kw in keywords)


# ---------------------------------------------------------------------------
# 2. 답변 중간 잘림 (truncation)
# ---------------------------------------------------------------------------

# 문장이 정상 종료된 것으로 보는 문자
_TERMINAL_CHARS = set(".?!…。？！；;:")
# 종결 문자 뒤에 붙을 수 있는 닫는 기호
_CLOSING_CHARS = set(')]}"\'’”」』〕】>*_`')
# 구두점 없이도 완결로 보는 한국어 종결 어미
_KO_SENTENCE_ENDINGS = (
    "습니다", "합니다", "입니다", "됩니다", "봅니다", "세요", "해요", "예요",
    "이에요", "네요", "어요", "아요", "지요", "죠", "있다", "없다", "이다",
)
# 이걸로 끝나면 잘렸을 가능성이 높은 접속/연결 표현
_DANGLING_TOKENS = (
    "그리고", "그러나", "하지만", "또한", "또는", "및", "때문에", "위해",
    "통해", "대해", "따라", "관련", "경우", "하여", "해서", "이며", "이고",
    "and", "or", "but", "the", "a", "an", "to", "of", "for", "with", "in", "on",
)


def is_truncated_answer(answer: str) -> bool:
    """답변이 문장 중간에 끊긴 것으로 보이면 True."""
    raw = _safe_str(answer).rstrip()
    if not raw:
        return False

    # 코드블록이 열린 채 끝났으면 잘림
    if raw.count("```") % 2 == 1:
        return True

    # 마크다운 표는 행 단위로 끝나는 게 정상
    last_line = raw.splitlines()[-1].strip()
    if last_line.startswith("|") and last_line.endswith("|"):
        return False
    # 목록 항목만 있고 내용이 비어 있으면 잘림
    if re.fullmatch(r"(?:[-*+]|\d+\.)\s*", last_line):
        return True

    # 뒤쪽 닫는 기호/공백 제거 후 실제 마지막 문자 확인
    tail = raw
    while tail and (tail[-1] in _CLOSING_CHARS or tail[-1].isspace()):
        tail = tail[:-1]
    if not tail:
        return False

    last_char = tail[-1]

    # 정상 종결 문자
    if last_char in _TERMINAL_CHARS:
        return False

    # 쉼표/중점 등으로 끝나면 잘림
    if last_char in set(",、，·:") or last_char == "-":
        return True

    # 괄호가 열린 채 끝났으면 잘림
    for open_c, close_c in (("(", ")"), ("[", "]"), ("{", "}")):
        if tail.count(open_c) > tail.count(close_c):
            return True

    # 한국어 종결 어미로 끝나면 완결로 간주
    if any(tail.endswith(e) for e in _KO_SENTENCE_ENDINGS):
        return False

    # 접속사/전치사 등으로 끝나면 잘림
    last_token = re.split(r"[\s]", tail)[-1].strip("*_`\"'")
    if last_token.lower() in _DANGLING_TOKENS:
        return True

    # 그 외: 구두점 없이 끝났으면 잘림으로 본다
    return True


# ---------------------------------------------------------------------------
# 3. 언어 혼용 (language mixing)
# ---------------------------------------------------------------------------

def has_language_mixing(
    answer: str,
    han_ratio_threshold: float = 0.02,
    han_count_threshold: int = 4,
) -> bool:
    """
    한국어 답변에 일본어(가나)나 한자가 부적절하게 섞이면 True.

    - 가나(히라가나/가타카나)는 1자만 나와도 혼용으로 본다.
    - 한자는 '(漢字)'처럼 괄호 안 병기는 정상으로 보고 제외한 뒤,
      남은 한자가 임계치를 넘으면 혼용으로 본다.
    """
    text = _strip_noise(_safe_str(answer))
    if not text.strip():
        return False

    # 한국어 답변일 때만 검사
    if detect_language(text) != "ko":
        return False

    if RE_KANA.search(text):
        return True

    # 괄호 안 한자 병기는 허용 → 제거
    text_wo_paren = re.sub(r"[(（][^)）]{0,20}[)）]", " ", text)
    han_chars = RE_HAN.findall(text_wo_paren)
    if not han_chars:
        return False

    letters = len(RE_HANGUL.findall(text_wo_paren)) + len(han_chars) + len(
        RE_LATIN.findall(text_wo_paren)
    )
    if letters == 0:
        return False

    return (
        len(han_chars) >= han_count_threshold
        and len(han_chars) / letters >= han_ratio_threshold
    )


# ---------------------------------------------------------------------------
# 4. 포맷 지시 불응
# ---------------------------------------------------------------------------

# (지시 감지 정규식, 준수 여부 판정 함수) 쌍
def _looks_like_table(ans: str) -> bool:
    lines = [l.strip() for l in ans.splitlines() if l.strip()]
    pipe_rows = [l for l in lines if l.startswith("|") and l.endswith("|")]
    if len(pipe_rows) >= 2:
        return True
    # HTML 표
    return bool(re.search(r"<table[\s>]", ans, re.IGNORECASE))


def _looks_like_bullets(ans: str) -> bool:
    lines = [l.strip() for l in ans.splitlines() if l.strip()]
    bullets = [l for l in lines if re.match(r"^(?:[-*•·▪]|\d+[.)])\s+", l)]
    return len(bullets) >= 2


def _looks_like_single_line(ans: str) -> bool:
    return len([l for l in ans.strip().splitlines() if l.strip()]) <= 1


def _looks_like_json(ans: str) -> bool:
    stripped = re.sub(r"^```(?:json)?|```$", "", ans.strip(), flags=re.MULTILINE).strip()
    return bool(re.match(r"^[\[{]", stripped) and re.search(r"[\]}]\s*$", stripped))


def _looks_like_numbered(ans: str) -> bool:
    lines = [l.strip() for l in ans.splitlines() if l.strip()]
    numbered = [l for l in lines if re.match(r"^\d+[.)]\s+", l)]
    return len(numbered) >= 2


_FORMAT_RULES: tuple[tuple[re.Pattern, Callable[[str], bool]], ...] = (
    # 표
    (re.compile(r"(표로|표\s*형식|테이블로|table\s*(형식|form)|as\s+a\s+table|in\s+a\s+table)", re.I),
     _looks_like_table),
    # 한 줄
    (re.compile(r"(한\s*줄로|한\s*문장으로|one\s*line|single\s*line|in\s+one\s+sentence)", re.I),
     _looks_like_single_line),
    # bullet / 목록
    (re.compile(r"(bullet|불릿|글머리|목록으로|리스트로|list\s*형식|as\s+a\s+list)", re.I),
     _looks_like_bullets),
    # 번호 매기기
    (re.compile(r"(번호를?\s*매겨|번호로|numbered\s*list|1\.\s*2\.\s*3\.)", re.I),
     _looks_like_numbered),
    # JSON
    (re.compile(r"(json|제이슨)", re.I), _looks_like_json),
)


def violates_format_instruction(query: str, answer: str) -> bool:
    """
    질의에 포맷 지시가 있는데 답변이 그 포맷을 따르지 않으면 True.
    질의는 앞 100자만 사용한다.
    """
    q = _safe_str(query)[:QUERY_HEAD_LEN]
    ans = _safe_str(answer)
    if not q.strip() or not ans.strip():
        return False

    for instruction_pat, checker in _FORMAT_RULES:
        if instruction_pat.search(q) and not checker(ans):
            return True
    return False


# ---------------------------------------------------------------------------
# 5. 민감정보(PII) 포함 여부 + 마스킹
# ---------------------------------------------------------------------------

PII_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b"),
    # 한국 휴대폰/유선 + 국제 표기
    "phone": re.compile(r"(?<!\d)(?:\+?82[-. ]?)?0?1[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)"),
    "phone_landline": re.compile(r"(?<!\d)0\d{1,2}[-. ]\d{3,4}[-. ]\d{4}(?!\d)"),
    # 주민등록번호
    "rrn": re.compile(r"(?<!\d)\d{6}[-\s]?[1-4]\d{6}(?!\d)"),
    # 카드번호 (16자리)
    "card": re.compile(r"(?<!\d)(?:\d{4}[-\s]?){3}\d{4}(?!\d)"),
    # 계좌번호 (10~14자리, 하이픈 포함)
    "account": re.compile(r"(?<!\d)\d{2,6}-\d{2,6}-\d{2,7}(?!\d)"),
    # 여권번호 (한국)
    "passport": re.compile(r"\b[MSRODmsrod]\d{8}\b"),
    "ipv4": re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"),
    # 사업자등록번호
    "biz_no": re.compile(r"(?<!\d)\d{3}-\d{2}-\d{5}(?!\d)"),
}

# 오탐이 잦은 패턴은 추가 검증
def _valid_ipv4(s: str) -> bool:
    return all(0 <= int(p) <= 255 for p in s.split("."))


def _luhn_ok(s: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", s)]
    if len(digits) != 16:
        return False
    total, parity = 0, len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def find_pii(answer: str) -> list[tuple[str, str]]:
    """탐지된 PII를 (종류, 원문) 리스트로 반환."""
    text = _safe_str(answer)
    if not text.strip():
        return []

    found: list[tuple[str, str]] = []
    for kind, pattern in PII_PATTERNS.items():
        for m in pattern.finditer(text):
            value = m.group(0)
            if kind == "ipv4" and not _valid_ipv4(value):
                continue
            if kind == "card" and not _luhn_ok(value):
                continue
            found.append((kind, value))
    return found


def contains_pii(answer: str) -> bool:
    """답변에 민감정보로 보이는 문자열이 있으면 True."""
    return len(find_pii(answer)) > 0


def mask_pii(answer: str, mask_char: str = "*", keep_tail: int = 0) -> str:
    """
    탐지된 PII를 마스킹한 문자열을 반환한다.
    이메일은 로컬파트만, 그 외는 전체(또는 뒤 keep_tail자리 유지)를 마스킹.
    """
    text = _safe_str(answer)
    for kind, value in sorted(find_pii(text), key=lambda x: -len(x[1])):
        if kind == "email":
            local, _, domain = value.partition("@")
            masked = (local[0] if local else "") + mask_char * max(len(local) - 1, 1) + "@" + domain
        else:
            body = re.sub(r"\w", mask_char, value)
            if keep_tail > 0 and len(value) > keep_tail:
                body = re.sub(r"\w", mask_char, value[:-keep_tail]) + value[-keep_tail:]
            masked = body
        text = text.replace(value, masked)
    return text


# ---------------------------------------------------------------------------
# 6. 질답 언어 불일치
# ---------------------------------------------------------------------------

def has_qa_language_mismatch(query: str, answer: str) -> bool:
    """질의 언어와 답변 언어가 다르면 True. 판별 불가면 False."""
    q_lang = detect_language(_safe_str(query)[:QUERY_HEAD_LEN])
    a_lang = detect_language(answer)

    if q_lang == "unknown" or a_lang == "unknown":
        return False
    return q_lang != a_lang


# ---------------------------------------------------------------------------
# 7. 유효하지 않은 링크
# ---------------------------------------------------------------------------

RE_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
RE_BARE_URL = re.compile(r"(?<![(\]])\b(?:https?://|www\.)[^\s<>\"'`)\]]+", re.IGNORECASE)

_PLACEHOLDER_HOSTS = (
    "example.com", "example.org", "example.net", "yourdomain",
    "localhost", "127.0.0.1", "test.com", "abc.com", "url.com",
)
_PLACEHOLDER_TOKENS = ("<", ">", "{", "}", "링크", "url_here", "insert", "your-", "xxx")
_VALID_TLD = re.compile(r"\.[a-z]{2,24}(?:$|[/:?#])", re.IGNORECASE)


def _is_invalid_url(url: str) -> bool:
    url = url.strip()
    if not url:
        return True
    low = url.lower()

    # 플레이스홀더/템플릿 흔적
    if any(t in low for t in _PLACEHOLDER_TOKENS):
        return True
    if any(h in low for h in _PLACEHOLDER_HOSTS):
        return True

    # 스킴 검사
    if not re.match(r"^(?:https?://|www\.|/)", low):
        return True
    # 스킴 오타 (htp://, http:/, https//)
    if re.match(r"^(?:htt?ps?:/(?!/)|htt?ps?//|ht+ps?:)", low):
        return True

    # 호스트 추출
    host = re.sub(r"^https?://", "", low)
    host = host.split("/")[0].split("?")[0].split("#")[0]
    if not host:
        return True
    if " " in url:
        return True
    if not _VALID_TLD.search(host + "/"):
        return True
    # 점으로 시작/끝나거나 연속 점
    if host.startswith(".") or host.endswith(".") or ".." in host:
        return True
    # 너무 짧게 끊긴 URL
    if low.rstrip("/") in ("http://", "https://", "www."):
        return True
    return False


def has_invalid_link(answer: str) -> bool:
    """답변에 형식이 깨졌거나 플레이스홀더인 링크가 있으면 True."""
    text = _safe_str(answer)
    if not text.strip():
        return False

    # 마크다운 링크
    for _, url in RE_MD_LINK.findall(text):
        if _is_invalid_url(url):
            return True

    # 마크다운 링크를 제거한 뒤 남은 맨 URL
    rest = RE_MD_LINK.sub(" ", text)
    for url in RE_BARE_URL.findall(rest):
        if _is_invalid_url(url):
            return True

    # 닫히지 않은 마크다운 링크: [텍스트](http... 로 끝남
    if re.search(r"\[[^\]]*\]\([^)]*$", text):
        return True
    return False


# ---------------------------------------------------------------------------
# 검사 레지스트리 & 일괄 적용
# ---------------------------------------------------------------------------

# (태그명, 함수, 질의 필요 여부)
CHECKS: tuple[tuple[str, Callable, bool], ...] = (
    ("include_error_keyword", has_no_info_keyword, False),
    ("truncated_answer", is_truncated_answer, False),
    ("language_mixing", has_language_mixing, False),
    ("format_violation", violates_format_instruction, True),
    ("contains_pii", contains_pii, False),
    ("qa_language_mismatch", has_qa_language_mismatch, True),
    ("invalid_link", has_invalid_link, False),
)


def evaluate_row(query: str, answer: str) -> list[str]:
    """한 행에 대해 모든 검사를 돌리고 True인 태그 리스트를 반환."""
    q = _safe_str(query)[:QUERY_HEAD_LEN]
    a = _safe_str(answer)

    tags: list[str] = []
    for tag, func, needs_query in CHECKS:
        try:
            hit = func(q, a) if needs_query else func(a)
        except Exception:
            hit = False
        if hit:
            tags.append(tag)
    return tags


def apply_flags(
    df,
    input_col: str = "input_msg_content",
    output_col: str = "output_msg_content",
    flag_col: str = "Flags",
    append: bool = True,
):
    """
    DataFrame의 각 행을 검사해 flag_col에 태그 리스트를 채운다.

    append=True 이면 기존 Flags 값에 이어붙이고, False이면 덮어쓴다.
    """
    def _existing(value) -> list[str]:
        if not append:
            return []
        if isinstance(value, list):
            return list(value)
        s = _safe_str(value).strip()
        if not s or s in ("[]", "nan"):
            return []
        try:
            import ast
            parsed = ast.literal_eval(s)
            return list(parsed) if isinstance(parsed, (list, tuple)) else [s]
        except (ValueError, SyntaxError):
            return [s]

    if flag_col not in df.columns:
        df[flag_col] = None

    new_flags = []
    for _, row in df.iterrows():
        tags = evaluate_row(row.get(input_col), row.get(output_col))
        merged = _existing(row.get(flag_col))
        for t in tags:
            if t not in merged:
                merged.append(t)
        new_flags.append(merged)

    df[flag_col] = new_flags
    return df


def run(
    csv_path: str,
    out_path: Optional[str] = None,
    input_col: str = "input_msg_content",
    output_col: str = "output_msg_content",
    flag_col: str = "Flags",
):
    """CSV를 읽어 플래그를 붙이고 저장한다."""
    import pandas as pd

    df = pd.read_csv(csv_path)
    df = apply_flags(df, input_col=input_col, output_col=output_col, flag_col=flag_col)

    if out_path:
        df.to_csv(out_path, index=False)

    # 태그별 집계 출력
    counts: dict[str, int] = {}
    for tags in df[flag_col]:
        for t in tags:
            counts[t] = counts.get(t, 0) + 1
    total = len(df)
    print(f"총 {total}행")
    for tag, _, _ in CHECKS:
        c = counts.get(tag, 0)
        print(f"  {tag:24s} {c:6d}  ({c / total * 100:5.1f}%)" if total else f"  {tag}: {c}")
    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM 답변 rule-based 품질 검사")
    parser.add_argument("csv_path", help="입력 CSV 경로")
    parser.add_argument("-o", "--out", default=None, help="출력 CSV 경로")
    parser.add_argument("--input-col", default="input_msg_content")
    parser.add_argument("--output-col", default="output_msg_content")
    parser.add_argument("--flag-col", default="Flags")
    args = parser.parse_args()

    run(
        args.csv_path,
        out_path=args.out,
        input_col=args.input_col,
        output_col=args.output_col,
        flag_col=args.flag_col,
    )
