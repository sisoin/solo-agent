"""기업 분석 에이전트(Supervisor) 전용 상태 정의."""
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class CompanyAnalysisState(TypedDict):
    # ── 입력 (상위 그래프 branch_companies → Send 로 주입) ──────────────────────
    company: str
    """분석 대상 회사명 (예: "LG에너지솔루션", "CATL")"""

    retrieved_docs: list[Document]
    """상위 그래프 retrieve 노드에서 전달된 공통 RAG 검색 결과."""

    # ── Supervisor LLM 대화 히스토리 (langgraph_supervisor 호환) ──────────────
    messages: Annotated[list[AnyMessage], add_messages]
    """Supervisor가 하위 에이전트를 tool-call 방식으로 조율할 때 사용하는 메시지 히스토리."""

    # ── 하위 에이전트 결과 ─────────────────────────────────────────────────────
    market_analysis: str
    """market_analysis_agent가 생성한 최종 시장 분석 보고서.
    글로벌 시장 규모·성장률, 지역별 수요, 원자재 가격, 시장 점유율, 규제 등 포함."""

    tech_analysis: str
    """tech_analysis_agent가 생성한 최종 기술 역량 분석 결과.
    RAG 기반으로 배터리 기술(셀 화학, 에너지 밀도, 생산 공정 등)을 평가한 텍스트."""

    # SWOT 세부 항목 — 후속 처리(비교·보고서)에서 항목별 접근이 필요할 때 사용
    strengths: list[str]
    """swot_analysis_agent — 내부 강점 항목 목록."""

    weaknesses: list[str]
    """swot_analysis_agent — 내부 약점 항목 목록."""

    opportunities: list[str]
    """swot_analysis_agent — 외부 기회 항목 목록."""

    threats: list[str]
    """swot_analysis_agent — 외부 위협 항목 목록."""

    swot_matrix: str
    """swot_analysis_agent가 포맷한 최종 2×2 SWOT 행렬 문자열."""

    # ── 최종 출력 ──────────────────────────────────────────────────────────────
    company_report: str
    """market_analysis + tech_analysis + swot_matrix 를 Supervisor LLM이 종합한
    단일 기업 분석 보고서. company_comparison_agent 및 report_generation_agent에 전달된다."""
