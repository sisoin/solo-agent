"""
회사 비교 에이전트

역할:
    LG에너지솔루션과 CATL 각각의 기업 분석 에이전트
    (company_analysis_agent)가 반환한 결과를 받아 두 회사를 비교 분석한다.

입력:
    state["company_report"]["LG에너지솔루션"]: LG에너지솔루션 기업 분석 결과
    state["company_report"]["CATL"]          : CATL 기업 분석 결과

출력:
    state["comparison_report"]: 비교 분석 결과 (형식 미정)

NOTE:
    - 비교 항목은 미정
    - 두 company_analysis_agent가 모두 완료된 후 실행되어야 함
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
