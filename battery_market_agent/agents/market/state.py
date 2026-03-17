"""시장 분석 에이전트 전용 상태 정의."""
from typing import Annotated
from operator import add
from typing_extensions import TypedDict


class MarketAnalysisState(TypedDict):
    # ── 입력 ──────────────────────────────────────────────────────────────────
    company: str
    """분석 대상 회사명 (예: "LG에너지솔루션", "CATL")"""

    # ── 웹 검색 원시 결과 ──────────────────────────────────────────────────────
    market_size_raw: str
    """글로벌 배터리 시장 규모·성장률 웹 검색 원시 텍스트.
    예: "2024년 글로벌 배터리 시장 1,350억 달러, CAGR 18.5% ..." """

    regional_demand_raw: str
    """중국·유럽·북미 지역별 수요 동향 웹 검색 원시 텍스트."""

    raw_material_prices_raw: str
    """리튬·코발트·니켈 원자재 가격 웹 검색 원시 텍스트."""

    company_market_share_raw: str
    """대상 기업의 글로벌 시장 점유율 웹 검색 원시 텍스트.
    예: "CATL 39.2% (2025), LG에너지솔루션 9.2% (2025, 3위)" """

    battery_price_per_kwh_raw: str
    """배터리 팩 가격($/kWh) 추이 웹 검색 원시 텍스트.
    예: "2025년 $108/kWh (전년비 -8%), 2026년 $105/kWh 전망 — BloombergNEF" """

    regulatory_policy_raw: str
    """주요 배터리 규제·정책 웹 검색 원시 텍스트.
    예: EU Battery Regulation 2026 라벨링 의무, IRA 세액공제 요건 등"""

    news_items: Annotated[list[str], add]
    """최신 배터리 산업 뉴스·이슈 목록. 검색 호출마다 누적(add)된다."""

    # ── 출처 ───────────────────────────────────────────────────────────────────
    market_sources: dict[str, list[dict[str, str]]]
    """기업별 출처 목록. 키: 회사명, 값: [{"title": str, "url": str, "tool": str}, ...]
    tool 값: "search_web" | "fetch_google_news"
    URL은 실제 접속 가능한 주소만 포함한다."""

    # ── 최종 결과 ──────────────────────────────────────────────────────────────
    market_analysis: str
    """LLM이 위 수집 데이터를 종합한 최종 시장 분석 보고서 (한국어, 항목별 구조화)."""
