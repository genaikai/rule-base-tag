"""태거 베이스 클래스."""

from abc import ABC, abstractmethod


class Tagger(ABC):
    """모든 태거가 상속해야 하는 베이스 클래스.

    각 태거는 입력 행들을 읽고 특정 조건에 대해 판정하며,
    통계 정보를 딕셔너리 형태로 반환한다.
    """

    name: str  # 태거 이름. 서브클래스에서 반드시 정의 (예: "sensitive_info")

    @abstractmethod
    def tag(self, rows: list[dict]) -> dict:
        """행 데이터를 태깅하고 결과를 반환한다.

        Args:
            rows: 입력 행 리스트 (각 행은 dict)

        Returns:
            dict with keys:
                - count: int, 태그 해당하는 행의 개수
                - rows: list[int], 해당 행의 인덱스 (선택)
                - note: str, 추가 설명 (선택)
                기타 필요한 메트릭 자유롭게 추가
        """
        pass
