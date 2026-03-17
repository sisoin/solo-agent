"""기업 비교 에이전트 전용 상태 정의."""
from typing_extensions import TypedDict


class SWOTItems(TypedDict):
    """단일 기업 SWOT 세부 항목 모음."""

    strengths: list[str]
    """내부 강점 항목 목록."""

    weaknesses: list[str]
    """내부 약점 항목 목록."""

    opportunities: list[str]
    """외부 기회 항목 목록."""

    threats: list[str]
    """외부 위협 항목 목록."""

    swot_matrix: str
    """포맷된 2×2 SWOT 행렬 문자열."""


class CompanyComparisonState(TypedDict):
    # ── 입력 (company_analysis_agent ×2 병렬 완료 후 합류) ────────────────────
    company_report: dict[str, str]
    """기업별 종합 분석 보고서.
    {"LG에너지솔루션": "<보고서>", "CATL": "<보고서>"}"""

    market_analysis_by_company: dict[str, str]
    """기업별 시장 분석 텍스트.
    {"LG에너지솔루션": "<시장 분석>", "CATL": "<시장 분석>"}"""

    tech_analysis_by_company: dict[str, str]
    """기업별 기술 역량 분석 텍스트.
    {"LG에너지솔루션": "<기술 분석>", "CATL": "<기술 분석>"}"""

    swot_by_company: dict[str, SWOTItems]
    """기업별 SWOT 세부 항목.
    {"LG에너지솔루션": SWOTItems, "CATL": SWOTItems}"""

    # ── 비교 기준 (미정) ─────────────────────────────────────────────────────
    # TODO: 비교 평가 기준 확정 후 이 섹션에 필드 추가
    # 예시 후보:
    #   comparison_dimensions: list[str]   — 비교할 차원 목록 (기술력, 원가, 지역 등)
    #   scoring_rubric: dict[str, Any]     — 차원별 평가 루브릭

    # ── 최종 출력 ────────────────────────────────────────────────────────────
    comparison_report: str
    """두 기업을 종합 비교 분석한 최종 텍스트.
    report_generation_agent의 ReportState.comparison_report 필드로 전달된다."""
