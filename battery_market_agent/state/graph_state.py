"""
BatteryMarketState — 최상위 그래프 전체 공유 상태.

필드별 수명:
    retrieved_docs   : retrieve_node → (Send로 복사) → company_analysis ×2
    company          : Send API가 각 company_analysis 브랜치에 주입
    company_report   : company_analysis ×2 병렬 결과 → _merge_dicts로 합산
    comparison_report: company_comparison_agent → report_generation_agent
    final_report     : report_generation_agent → END
    report_*_path    : report_generation_agent → END
"""
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.documents import Document


def _merge_dicts(left: dict, right: dict) -> dict:
    """두 dict를 병합한다. 오른쪽 값이 왼쪽을 덮어씌운다."""
    return {**left, **right}


class BatteryMarketState(TypedDict):
    # ── retrieve 단계 ─────────────────────────────────────────────────────
    retrieved_docs: list[Document]
    """retrieve_node가 수집한 공통 RAG 검색 결과.
    branch_companies(Send)로 각 company_analysis 브랜치에 그대로 전달된다."""

    # ── company_analysis 병렬 분기 ────────────────────────────────────────
    company: str
    """Send API가 주입하는 현재 처리 중인 회사명.
    ("LG에너지솔루션" | "CATL")"""

    company_report: Annotated[dict[str, str], _merge_dicts]
    """기업별 종합 분석 보고서.
    {"LG에너지솔루션": "<보고서>", "CATL": "<보고서>"}
    두 병렬 브랜치가 각각 단일 키를 반환하며 _merge_dicts로 합산된다."""

    market_trends: Annotated[dict[str, str], _merge_dicts]
    """기업별 시장 동향 분석 텍스트.
    {"LG에너지솔루션": "<분석>", "CATL": "<분석>"}"""

    market_sources: Annotated[dict[str, list], _merge_dicts]
    """기업별 웹 검색 출처 목록.
    {"LG에너지솔루션": [{"title", "url", "tool"}, ...], "CATL": [...]}"""

    rag_sources: list[dict]
    """retrieve_node가 수집한 RAG 문서 출처 목록.
    [{"source": "<path|url>", "company": "<회사명|None>", "filename": "<파일명>"}, ...]
    보고서 참고문헌에 반드시 포함된다."""

    # ── company_comparison 단계 ───────────────────────────────────────────
    comparison_report: str
    """company_comparison_agent가 생성한 두 기업 비교 분석 텍스트."""

    # ── report_generation 단계 ────────────────────────────────────────────
    final_report: str
    """report_generation_agent가 생성한 보고서 SUMMARY 텍스트."""

    report_pdf_path: str
    """저장된 PDF 보고서 파일 경로."""
