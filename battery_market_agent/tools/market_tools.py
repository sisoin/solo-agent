"""
에이전트에 바인딩되는 배터리 시장 분석 도구 모음.

각 함수는 @tool (LangChain)로 데코레이팅되어
에이전트의 도구 목록에 직접 전달됩니다.
"""
from langchain_core.tools import tool


@tool
def search_battery_market_data(query: str) -> str:
    """배터리 시장 규모, 성장률, 세그먼트 데이터를 검색합니다."""
    # TODO: 구현 — 웹 검색 또는 벡터 저장소 조회
    raise NotImplementedError


@tool
def analyze_competitors(company_names: list[str]) -> str:
    """지정된 배터리 기업들의 경쟁 포지셔닝을 분석합니다."""
    # TODO: 구현 — 구조화된 경쟁사 분석
    raise NotImplementedError


@tool
def fetch_price_trends(material: str, period: str = "1y") -> str:
    """배터리 원자재(예: 리튬, 코발트)의 역사적 가격 추이를 조회합니다."""
    # TODO: 구현 — yfinance / Finance DataReader
    raise NotImplementedError


@tool
def summarize_regulations(region: str) -> str:
    """특정 지역의 배터리 관련 규제 및 정책을 요약합니다."""
    # TODO: 구현 — 규제 문서에 대한 RAG 검색
    raise NotImplementedError
