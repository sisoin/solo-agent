"""
시장 분석 에이전트

역할:
    웹 서치 도구(search_web, fetch_google_news)를 활용해
    LG에너지솔루션·CATL의 최신 시장 동향을 수집·분석한다.

수집 대상:
    - 글로벌 배터리 시장 규모 및 성장률
    - 주요 지역별 수요 동향 (중국, 유럽, 북미)
    - 원자재 가격 동향 (리튬, 코발트, 니켈)
    - 최신 뉴스 및 산업 이슈

출력:
    state["market_trends"]: 회사별 시장 동향 요약 (dict)
"""
from battery_market_agent.state import BatteryMarketState
from battery_market_agent.tools import search_web, fetch_google_news, fetch_price_trends

MARKET_TOOLS = [search_web, fetch_google_news, fetch_price_trends]


def market_analysis_agent(state: BatteryMarketState) -> dict:
    """
    시장 분석 에이전트 노드.

    TODO:
    - state["company"] 기반으로 검색 쿼리 구성
    - MARKET_TOOLS를 바인딩한 LLM으로 ReAct 루프 실행
    - 수집된 시장 동향을 state["market_trends"]에 저장
    """
    raise NotImplementedError
