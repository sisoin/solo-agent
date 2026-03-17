"""
SWOT 분석 에이전트

역할:
    시장 분석 에이전트가 수집한 기업 정보를 바탕으로
    LG에너지솔루션·CATL 각각의 SWOT 분석을 수행하고
    마크다운 표 형태로 결과를 반환한다.

입력:
    state["market_trends"]: 시장 분석 에이전트 결과
    state["retrieved_docs"]: RAG 검색 문서

출력:
    state["swot_table"]: 마크다운 표 문자열 (회사별 SWOT)

출력 예시:
    | 구분           | 강점 (S) | 약점 (W) | 기회 (O) | 위협 (T) |
    |----------------|----------|----------|----------|----------|
    | LG에너지솔루션 | ...      | ...      | ...      | ...      |
    | CATL           | ...      | ...      | ...      | ...      |
"""
from battery_market_agent.state import BatteryMarketState

SWOT_CATEGORIES = ["강점 (Strength)", "약점 (Weakness)", "기회 (Opportunity)", "위협 (Threat)"]


def swot_analysis_agent(state: BatteryMarketState) -> dict:
    """
    SWOT 분석 에이전트 노드.

    TODO:
    - state["market_trends"]와 state["retrieved_docs"]를 컨텍스트로 LLM 호출
    - SWOT_CATEGORIES 기준으로 두 회사 각각 분석
    - 결과를 마크다운 표로 포맷팅하여 state["swot_table"]에 저장
    """
    raise NotImplementedError
