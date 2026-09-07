"""모든 태거를 로드하고 관리하는 모듈."""

from .base import Tagger
from .sensitive_info import SensitiveInfoTagger
from .error_keyword import ErrorKeywordTagger
from .answer_truncated import AnswerTruncatedTagger
from .language_mixing import LanguageMixingTagger
from .format_broken import FormatBrokenTagger
from .empty_retrieved_docs import EmptyRetrievedDocsTagger
from .empty_search_query import EmptySearchQueryTagger
from .language_mismatch import LanguageMismatchTagger
from .invalid_link import InvalidLinkTagger
from .model_thinking_stopped import ModelThinkingStoppedTagger

# 등록된 모든 태거. 새로운 태거는 여기에 추가
TAGGERS: list[Tagger] = [
    SensitiveInfoTagger(),
    ErrorKeywordTagger(),
    AnswerTruncatedTagger(),
    LanguageMixingTagger(),
    FormatBrokenTagger(),
    EmptyRetrievedDocsTagger(),
    EmptySearchQueryTagger(),
    LanguageMismatchTagger(),
    InvalidLinkTagger(),
    ModelThinkingStoppedTagger(),
]

__all__ = ["Tagger", "TAGGERS"]
