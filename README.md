# rule-based-tagging

**목표**: 사용자의 Query에 대한 LLM의 답변을 평가하여 다음과 같은 Tag를 부여합니다.

## 📋 Tag 종류

- **에러 키워드**: 답변 내 오류나 잘못된 정보 포함
- **답변 잘림**: 생성된 답변이 중간에 끊김
- **언어 Mixing**: 답변에서 언어가 섞임
- **Format 깨짐**: 테이블 등 구조화된 포맷이 손상됨
- **민감정보 포함**: 개인정보, 보안정보 등 민감한 정보 포함
- **Empty Retrieved Docs**: 검색 결과가 없음
- **Empty Search Query**: 검색 쿼리가 비어있음
- **질답 언어 불일치**: Query와 답변의 언어가 다름
- **유효하지 않은 링크**: 제시된 링크가 유효하지 않음
- **모델 생각중 멈춤**: 모델이 생각 중에 멈춰 답변을 받지 못함

## 🏷️ Tag 표시법

- **평가 방식**: Boolean 형식 (True/False)
- **True**: 해당 Tag에 해당하는 문제가 있음
- **False**: 해당 Tag에 해당하는 문제가 없음

---

## 어디에 있나

태그 하나가 폴더 하나다. 폴더 안의 `_hit(row)` 이 그 태그의 True/False 를 정한다.

| Tag | 폴더 | 읽는 필드 |
|---|---|---|
| 에러 키워드 | `features/error_keyword/` | `answer` |
| 답변 잘림 | `features/answer_truncated/` | `answer` |
| 언어 Mixing | `features/language_mixing/` | `answer` |
| Format 깨짐 | `features/format_broken/` | `answer` |
| 민감정보 포함 | `features/sensitive_info/` | `answer` |
| Empty Retrieved Docs | `features/empty_retrieved_docs/` | `retrieved_docs` |
| Empty Search Query | `features/empty_search_query/` | `search_query` |
| 질답 언어 불일치 | `features/language_mismatch/` | `query` + `answer` |
| 유효하지 않은 링크 | `features/invalid_link/` | `answer` |
| 모델 생각중 멈춤 | `features/model_thinking_stopped/` | `query` + `answer` |

전부 `src/rule_base_tag/` 아래에 있다.

```
src/run.py                    진입점
src/rule_base_tag/
    schema.py                 입력 스키마 — 컬럼 이름의 유일한 출처
    synth.py                  가짜 데이터 (파일이 아니라 코드다)
    load.py                   CSV 읽기
    report.py                 RUN SUMMARY
    pipeline.py               판정들을 불러 한 장으로 합친다
    features/
        _shared.py            판정 둘 이상이 같이 쓰는 것
        template/             새 판정을 만들 때 복사하는 원본
        <태그>/               판정 하나
```

## 무엇을 고치나

| 하려는 일 | 고칠 곳 |
|---|---|
| 컬럼 이름이 실제 로그와 다르다 | `schema.py` 위쪽 상수 네 줄 |
| 어떤 태그의 판정 기준을 바꾼다 | `features/<태그>/__init__.py` 의 `_hit()` |
| 태그를 하나 추가한다 | 아래 "새 판정 추가" |
| 판정 순서를 바꾼다 | `pipeline.py` 의 `FEATURES` |

**고치지 않는 곳**: `load.py` · `report.py` · `__main__.py` · `src/run.py`.
판정이 몇 개가 되든 이 넷은 그대로다.

## 어떻게 돌리나

```bash
python src/run.py --dry-run                    # 가짜 데이터. 전 구간이 도는지
python src/run.py --dry-run --adversarial      # 판정 열 개가 다 살아있는지
python src/run.py --data <csv> --limit 1000    # 실데이터 일부로 스키마 확인
python src/run.py --data <csv>                 # 전체
```

종료 코드로 갈린다.

| 코드 | 뜻 |
|---|---|
| `0` | 정상 |
| `1` | 돌긴 했는데 스키마가 어긋났다. 숫자를 믿을 수 없다 |
| `2` | 시작도 못 했다 (인자 누락, 파일 없음) |

### 두 가짜 모드가 보증하는 것이 다르다

```
--dry-run                 열 개가 전부 0  ← 하나라도 켜지면 그 판정이 오탐이다
--dry-run --adversarial   열 개가 전부 켜짐 ← 하나라도 0 이면 그 판정이 죽은 것이다
```

판정을 고친 뒤에는 둘 다 돌려본다. 실데이터 없이 확인할 수 있는 것이 이 둘이다.

## 새 판정 추가

```bash
cp -r src/rule_base_tag/features/template src/rule_base_tag/features/<태그>
```

그리고 세 군데를 고친다.

1. `features/<태그>/__init__.py` — `NAME` 을 폴더 이름과 같게, `_hit()` 에 판정을
2. `pipeline.py` — import 와 `FEATURES` 에 한 줄씩
3. `synth.py` — `_d_<태그>()` 를 만들고 `_DEFECTS` 에 넣는다

3번을 빼먹으면 그 판정은 가짜 데이터에서 한 번도 켜지지 않는다. 그러면 규칙이 죽어도
`0` 으로 보이고, `0` 은 "문제가 없다" 와 구별되지 않는다.

**지표 이름은 `NAME` 으로 시작한다.** 결과가 한 리포트에 모이므로 이름이 겹치면
`pipeline.py` 가 `KeyError` 로 죽는다 — 조용히 덮어쓰는 것보다 낫다.

## 아직 안 된 것

- **스키마가 추정이다.** `schema.py` 의 컬럼 이름 네 개는 실제 로그를 보고 정한 것이
  아니다. `note` 에 "확인 필요" 라고 적힌 것들이 그렇다. 실데이터로 한 번 돌리면
  `schema` 줄에 어긋난 것이 이름과 숫자로 뜬다 — 그게 첫 사이클의 수확이다
- **행 단위 결과를 내보내지 못한다.** 지금 리포트는 태그마다 건수만 낸다.
  "답변 한 행에 태그 열 개" 를 파일로 내려면 결과 파일을 가져올 수 있어야 하는데
  그게 안 되는 환경이다. 무엇을 화면에 담을지 정해야 한다
- **정규식·키워드 목록이 가정이다.** 실제 답변을 보고 좁히거나 넓혀야 한다.
  특히 `sensitive_info` 는 느슨하게 쓰면 숫자 컬럼에 걸린다 — 그 파일의 주석 참고
