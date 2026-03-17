"""보고서 생성 에이전트 전용 상태 정의."""
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 구조화 출력 스키마 (LLM.with_structured_output 용)
# ---------------------------------------------------------------------------

class StrategyRow(BaseModel):
    """전략 비교표 단일 항목."""
    lg: str = Field(description="LG에너지솔루션의 해당 전략 항목 내용")
    catl: str = Field(description="CATL의 해당 전략 항목 내용")


class SWOTDetail(BaseModel):
    """단일 기업 SWOT 세부 항목."""
    strength: str     = Field(description="S — 내부 강점")
    weakness: str     = Field(description="W — 내부 약점")
    opportunity: str  = Field(description="O — 외부 기회")
    threat: str       = Field(description="T — 외부 위협")


class ReportSections(BaseModel):
    """LLM 구조화 출력으로 한 번에 생성되는 보고서 섹션 전체."""

    # SUMMARY
    summary: str = Field(description="핵심 인사이트 3~5줄 요약")

    # 1. 시장 배경
    market_overview: str        = Field(description="1.1 글로벌 배터리 시장 현황 및 규모")
    market_trends: str          = Field(description="1.2 시장 구조 변화 및 핵심 트렌드")
    competitive_landscape: str  = Field(description="1.4 경쟁 구도 개요 (글로벌 Top 점유율 및 CATL·LGES 포지션)")

    # 2. 기업별 포트폴리오
    lg_portfolio: str   = Field(description="2.1.1 LG에너지솔루션 사업 포트폴리오 구성")
    lg_tech: str        = Field(description="2.1.2 LG에너지솔루션 기술 경쟁력")
    catl_portfolio: str = Field(description="2.2.1 CATL 사업 포트폴리오 구성")
    catl_tech: str      = Field(description="2.2.2 CATL 기술 경쟁력")

    # 3. 전략 비교
    strategy_tech: StrategyRow      = Field(description="기술 방향성 비교")
    strategy_region: StrategyRow    = Field(description="지역 전략 비교")
    strategy_customer: StrategyRow  = Field(description="고객 전략 비교")
    strategy_cost: StrategyRow      = Field(description="원가 전략 비교")
    strategy_new_biz: StrategyRow   = Field(description="신사업 방향 비교")

    # 3.2 SWOT
    swot_lg: SWOTDetail   = Field(description="LG에너지솔루션 SWOT 항목")
    swot_catl: SWOTDetail = Field(description="CATL SWOT 항목")
    swot_sw_implications: str = Field(description="3.2.3 내부 역량(S/W) 관점 비교 시사점")
    swot_ot_implications: str = Field(description="3.2.3 외부 환경(O/T) 관점 비교 시사점")

    # 4. 종합 시사점
    positioning_diff: str    = Field(description="4.1 두 기업의 전략적 포지셔닝 차이")
    market_outlook: str      = Field(description="4.2 배터리 시장 향후 전망과 시사점")
    investment_opinion: str  = Field(description="4.3 투자·협력 관점 종합 의견")

    # 참고문헌
    references: list[str] = Field(description="분석에 사용된 출처 목록")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class ReportState(TypedDict):
    # ── 입력 ────────────────────────────────────────────────────────────────
    company_report: dict[str, str]
    """기업 분석 Supervisor 결과. {"LG에너지솔루션": "...", "CATL": "..."}"""

    comparison_report: str
    """회사 비교 Supervisor 결과 (SWOT 포함 종합 비교 텍스트)."""

    # ── 구조화 섹션 ─────────────────────────────────────────────────────────
    sections: ReportSections | None
    """LLM with_structured_output으로 생성된 섹션 데이터. 포맷 전 중간 산출물."""

    # ── 최종 출력 ───────────────────────────────────────────────────────────
    final_report: str
    """sections를 보고서 양식(마크다운)으로 렌더링한 최종 텍스트."""

    report_md_path: str
    """저장된 마크다운 보고서 파일 경로."""

    report_pdf_path: str
    """저장된 PDF 보고서 파일 경로."""
