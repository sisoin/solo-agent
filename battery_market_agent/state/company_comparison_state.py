"""기업 비교 에이전트 전용 상태 정의."""
from typing_extensions import TypedDict


class CompanyComparisonState(TypedDict):
    # ── 입력 (company_analysis_agent ×2 병렬 완료 후 합류) ────────────────────
    company_report: dict[str, str]
    """기업별 종합 분석 보고서.
    {"LG에너지솔루션": "<보고서>", "CATL": "<보고서>"}"""

    # ── 최종 출력 ────────────────────────────────────────────────────────────
    comparison_report: str
    """두 기업을 종합 비교 분석한 최종 텍스트.
    report_generation_agent의 ReportState.comparison_report 필드로 전달된다."""
