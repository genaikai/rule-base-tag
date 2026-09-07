"""판정들을 불러 한 장으로 합친다.

기능 하나하나는 `features/<기능>/` 안에 있고, 이 파일은 그것들을 부르는 일만 한다.
목록이 여기 있는 것이 요점이다 — 기능이 늘어도 계약·적재·리포트·진입점은 손대지 않는다.

지표 이름은 기능마다 자기 이름을 접두어로 달고 온다. 안 그러면 `update()` 에서
조용히 덮어써서, 화면에는 마지막 기능의 숫자만 남는다.
"""

from .features import (
    answer_truncated,
    empty_retrieved_docs,
    empty_search_query,
    error_keyword,
    format_broken,
    invalid_link,
    language_mismatch,
    language_mixing,
    model_thinking_stopped,
    sensitive_info,
)

# 화면에 뜨는 순서다. 사람이 사이클 사이에 눈으로 대조하므로 순서를 바꾸지 않는다.
FEATURES = (
    error_keyword,
    answer_truncated,
    language_mixing,
    format_broken,
    sensitive_info,
    empty_retrieved_docs,
    empty_search_query,
    language_mismatch,
    invalid_link,
    model_thinking_stopped,
)


def process_data(rows: list[dict]) -> dict:
    """판정 전부를 한 번의 훑기로 돌리고 지표를 합친다."""
    metrics = {"rows": f"{len(rows):,}"}
    for feature in FEATURES:
        result = feature.process_data(rows)
        collided = metrics.keys() & result.keys()
        if collided:
            # 조용히 덮어쓰면 화면의 숫자가 거짓이 된다. 시끄럽게 죽는 쪽이 낫다.
            raise KeyError(f"{feature.NAME} 의 지표 이름이 겹친다: {sorted(collided)}")
        metrics.update(result)
    return metrics
