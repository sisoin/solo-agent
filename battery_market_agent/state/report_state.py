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
    market_overview: str       = Field(description=(
        "1.1 글로벌 배터리 시장 현황 및 규모. 700자 이상, 3문단 이상. "
        "시장 규모(달러 기준), 연평균 성장률(CAGR), 주요 성장 드라이버(EV 수요·ESS·정책)를 "
        "구체적 수치와 함께 서술."
    ))
    market_trends: str         = Field(description=(
        "1.2 시장 구조 변화 및 핵심 트렌드. 700자 이상, 3문단 이상. "
        "LFP vs NCM 점유율 변화, 전고체 배터리 동향, ESS 수요 확대, 원자재 가격 변동 등 "
        "3개 이상 트렌드를 각각 구체적으로 서술."
    ))
    competitive_landscape: str = Field(description=(
        "1.3 경쟁 구도 개요. 700자 이상, 3문단 이상. "
        "글로벌 Top 5 배터리 제조사 시장 점유율(수치 포함), "
        "CATL·LGES의 지역별 포지션 및 경쟁 구도를 서술."
    ))

    # 2. 기업별 포트폴리오
    lg_portfolio: str   = Field(description=(
        "2.1.1 LG에너지솔루션 사업 포트폴리오 구성. 700자 이상, 3문단 이상. "
        "파우치·원통형·각형 폼팩터 비중, EV·ESS·소형전지 매출 구조, 주요 고객사(OEM) 및 JV 현황을 서술. "
        "매출 부진·고객 이탈·가동률 하락 등 부정적 사업 현황도 반드시 포함."
    ))
    lg_tech: str        = Field(description=(
        "2.1.2 LG에너지솔루션 기술 경쟁력. 700자 이상, 3문단 이상. "
        "NCM·NCMA 양극재 기술, 건식전극 공정, 전고체 배터리 개발 로드맵, BMS 강점을 서술. "
        "기술 격차·상용화 지연·경쟁사 대비 열위 항목 등 기술적 한계도 반드시 포함."
    ))
    catl_portfolio: str = Field(description=(
        "2.2.1 CATL 사업 포트폴리오 구성. 700자 이상, 3문단 이상. "
        "LFP·NCM·나트륨이온 배터리 라인업, 각형 셀 주력 폼팩터, 글로벌 주요 OEM 고객사 및 해외 공장 현황을 서술. "
        "북미 시장 규제 리스크·수익성 압박·지정학적 리스크 등 부정적 사업 현황도 반드시 포함."
    ))
    catl_tech: str      = Field(description=(
        "2.2.2 CATL 기술 경쟁력. 700자 이상, 3문단 이상. "
        "셀투팩(CTP) 기술, 기린 배터리(Kirin), 나트륨이온·불소리튬(NFPP) 차세대 배터리, 공정 혁신을 서술. "
        "고밀도 배터리 분야 경쟁사 대비 열위·전고체 기술 격차 등 기술적 한계도 반드시 포함."
    ))

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
    positioning_diff: str   = Field(description=(
        "4.1 두 기업의 전략적 포지셔닝 차이. 700자 이상, 3문단 이상. "
        "지역(중국·북미·유럽), 배터리 화학(LFP vs NCM), 고객 전략 3개 축에서 "
        "구체적 수치·사례와 함께 비교 서술."
    ))
    market_outlook: str     = Field(description=(
        "4.2 배터리 시장 향후 전망과 시사점. 700자 이상, 3문단 이상. "
        "2025~2030년 시장 성장 전망, 양사의 기회 요인과 리스크 요인을 "
        "균형 있게 서술."
    ))
    investment_opinion: str = Field(description=(
        "4.3 투자·협력 관점 종합 의견. 700자 이상, 3문단 이상. "
        "양사의 투자 매력도, 주요 리스크, 협력 가능 영역을 "
        "투자자·파트너 관점에서 구체적으로 서술."
    ))

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
    rag_sources: list[dict]          # RAG 문서 출처 목록 — 반드시 참고문헌에 포함

    # ── 구조화 섹션 (중간 산출물) ─────────────────────────────────────────
    sections: ReportSections | None

    # ── 최종 출력 ───────────────────────────────────────────────────────────
    final_report: str
    report_pdf_path: str
