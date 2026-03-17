"""
회사 비교 에이전트

역할:
    LG에너지솔루션, CATL 각각의 기업 분석 에이전트(company_analysis_agent)가
    병렬로 완료된 후 두 결과를 받아 비교 분석을 수행한다.

입력:
    state["company_report"]["LG에너지솔루션"]: LG에너지솔루션 기업 분석 결과
    state["company_report"]["CATL"]          : CATL 기업 분석 결과

출력:
    state["comparison_report"]: 비교 분석 결과 (형식 미정)

NOTE:
    - 비교 항목 미정
    - LG에너지솔루션 / CATL company_analysis_agent 둘 다 완료된 후 실행
"""
from battery_market_agent.state import BatteryMarketState

COMPANIES = ["LG에너지솔루션", "CATL"]


def company_comparison_agent(state: BatteryMarketState) -> dict:
    """
    회사 비교 에이전트 노드.

    TODO:
    - 비교 항목 정의
    - COMPANIES 기준으로 state["company_report"] 각각 참조
    - LLM으로 두 회사 비교 분석 수행
    - 결과를 state["comparison_report"]에 저장
    """
    raise NotImplementedError
