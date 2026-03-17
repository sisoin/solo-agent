"""기술 분석 에이전트 전용 상태 정의."""
from typing import Annotated
from operator import add
from typing_extensions import TypedDict
from langchain_core.documents import Document


class TechAnalysisState(TypedDict):
    company: str                                     # 분석 대상 회사명
    tech_queries: list[str]                          # RAG 검색에 사용할 기술 쿼리 목록
    retrieved_docs: Annotated[list[Document], add]   # 쿼리별 RAG 검색 결과 누적
    tech_analysis: str                               # 최종 기술 분석 결과 (형식 미정)
