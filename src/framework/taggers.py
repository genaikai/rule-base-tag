"""모든 태거를 동적으로 로드하는 orchestrator."""

from .base import Tagger
from ..error_keyword import ErrorKeywordTagger
from ..answer_truncated import AnswerTruncatedTagger
from ..language_mixing import LanguageMixingTagger
from ..format_broken import FormatBrokenTagger
from ..empty_retrieved_docs import EmptyRetrievedDocsTagger
from ..empty_search_query import EmptySearchQueryTagger
from ..language_mismatch import LanguageMismatchTagger
from ..invalid_link import InvalidLinkTagger
from ..model_thinking_stopped import ModelThinkingStoppedTagger
from ..sensitive_info import SensitiveInfoTagger

# 등록된 모든 태거. 새로운 태거는 여기에 추가
TAGGERS: list[Tagger] = [
    ErrorKeywordTagger(),
    AnswerTruncatedTagger(),
    LanguageMixingTagger(),
    FormatBrokenTagger(),
    EmptyRetrievedDocsTagger(),
    EmptySearchQueryTagger(),
    LanguageMismatchTagger(),
    InvalidLinkTagger(),
    ModelThinkingStoppedTagger(),
    SensitiveInfoTagger(),
]

__all__ = ["Tagger", "TAGGERS"]
