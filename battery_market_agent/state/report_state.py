"""보고서 생성 에이전트 전용 상태 정의."""
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 구조화 출력 스키마 (LLM.with_structured_output 용)
# ---------------------------------------------------------------------------

class StrategyRow(BaseModel):
    """전략 비교표 단일 항목."""
    lg: str = Field(description="LG에너지솔루션의 해당 전략 항목 내용 (2~3문장)")
    catl: str = Field(description="CATL의 해당 전략 항목 내용 (2~3문장)")


class SWOTDetail(BaseModel):
    """단일 기업 SWOT 세부 항목."""
    strength: str     = Field(description="S — 내부 강점: 내부적으로 잘하고 있는 것, 경쟁 우위 요소")
    weakness: str     = Field(description="W — 내부 약점: 내부적으로 부족한 점, 개선이 필요한 부분")
    opportunity: str  = Field(description="O — 외부 기회: 외부 환경에서 유리하게 작용하는 요소")
    threat: str       = Field(description="T — 외부 위협: 외부 환경에서 위험 요소")


class ReportSections(BaseModel):
    """LLM 구조화 출력으로 한 번에 생성되는 보고서 섹션 전체."""

    # SUMMARY — 보고서 맨 앞, 1/2페이지 이내
    summary: str = Field(
        description=(
            "전체 전략 분석 보고서의 핵심 요약. "
            "1/2 페이지를 넘지 않도록 200자 내외로 작성. "
            "개요 장표가 아닌 핵심 인사이트 위주로 기술."
        )
    )

    # 1. 시장 배경
    market_overview: str       = Field(description="1.1 글로벌 배터리 시장 현황 및 규모 (수치 포함)")
    market_trends: str         = Field(description="1.2 시장 구조 변화 및 핵심 트렌드")
    competitive_landscape: str = Field(description="1.3 경쟁 구도 개요 (글로벌 Top 점유율 및 CATL·LGES 포지션)")

    # 2. 기업별 포트폴리오
    lg_portfolio: str   = Field(description="2.1.1 LG에너지솔루션 사업 포트폴리오 구성")
    lg_tech: str        = Field(description="2.1.2 LG에너지솔루션 기술 경쟁력")
    catl_portfolio: str = Field(description="2.2.1 CATL 사업 포트폴리오 구성")
    catl_tech: str      = Field(description="2.2.2 CATL 기술 경쟁력")

    # 3. 전략 비교
    strategy_tech: StrategyRow      = Field(description="기술 방향성 비교 (배터리 화학·폼팩터·차세대 기술)")
    strategy_region: StrategyRow    = Field(description="지역 전략 비교 (중국·유럽·북미 포지셔닝)")
    strategy_customer: StrategyRow  = Field(description="고객 전략 비교 (OEM 파트너십·고객 다변화)")
    strategy_cost: StrategyRow      = Field(description="원가 전략 비교 (수직계열화·공정 효율화)")
    strategy_new_biz: StrategyRow   = Field(description="신사업 방향 비교 (ESS·재활용·소재)")

    # 3.2 SWOT
    swot_lg: SWOTDetail   = Field(description="LG에너지솔루션 SWOT — S/W는 내부 요인, O/T는 외부 요인")
    swot_catl: SWOTDetail = Field(description="CATL SWOT — S/W는 내부 요인, O/T는 외부 요인")
    swot_sw_implications: str = Field(description="내부 역량(S/W) 관점 양사 비교 시사점")
    swot_ot_implications: str = Field(description="외부 환경(O/T) 관점 양사 비교 시사점")

    # 4. 종합 시사점
    positioning_diff: str   = Field(description="4.1 두 기업의 전략적 포지셔닝 차이")
    market_outlook: str     = Field(description="4.2 배터리 시장 향후 전망과 시사점")
    investment_opinion: str = Field(description="4.3 투자·협력 관점 종합 의견")

    # REFERENCE — 보고서 맨 마지막
    references: list[str] = Field(
        description=(
            "실제로 활용한 자료 목록만 기재. 형식:\n"
            "  기관 보고서 : 발행기관(YYYY). 보고서명. URL\n"
            "  학술 논문  : 저자(YYYY). 논문제목. 학술지명, 권(호), 페이지.\n"
            "  웹페이지   : 기관명 또는 작성자(YYYY-MM-DD). 제목. 사이트명, URL"
        )
    )


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class ReportState(TypedDict):
    # ── 입력 ────────────────────────────────────────────────────────────────
    company_report: dict[str, str]
    comparison_report: str
    market_sources: dict[str, list]  # 기업별 웹 검색 출처 목록

    # ── 구조화 섹션 (중간 산출물) ─────────────────────────────────────────
    sections: ReportSections | None

    # ── 최종 출력 ───────────────────────────────────────────────────────────
    final_report: str
    report_pdf_path: str
