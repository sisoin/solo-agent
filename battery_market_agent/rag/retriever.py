"""
TODO: BatteryRAG 정의

RAG 파이프라인 구성 요소:
- 문서 로딩 (PDF, 웹, 리포트)
- 텍스트 분할 및 임베딩
- 벡터 저장소 (Chroma / FAISS)
- 유사도 검색 기반 리트리버
"""
from battery_market_agent.config import Settings


class BatteryRAG:
    """
    TODO: 배터리 시장 문서를 위한 RAG 파이프라인 구현.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        # TODO: 벡터 저장소 및 리트리버 초기화

    def load_documents(self, source: str):
        """TODO: 배터리 시장 리포트 / 데이터 소스 로딩."""
        raise NotImplementedError

    def build_index(self):
        """TODO: 문서 임베딩 후 벡터 인덱스 구축."""
        raise NotImplementedError

    def retrieve(self, query: str) -> list:
        """TODO: 쿼리에 대한 상위 k개 관련 문서 검색."""
        raise NotImplementedError
