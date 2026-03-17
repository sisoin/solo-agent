"""
보고서 생성 에이전트

역할:
    기업 분석 에이전트(company_analysis_agent)가 회사 비교 에이전트에 전달한 값과
    회사 비교 에이전트(company_comparison_agent)가 보고서 생성 에이전트에 전달한 값을
    종합하여 최종 전략 보고서를 생성한다.

입력:
    state["company_report"]    : 기업 분석 에이전트 결과 (LG에너지솔루션 / CATL 각각)
    state["comparison_report"] : 회사 비교 에이전트 결과

출력:
    state["final_report"]: 최종 보고서 (목차 및 양식 미정)

NOTE:
    - 보고서 목차 및 출력 포맷은 미정
    - company_comparison_agent 완료 후 실행되어야 함
"""
from battery_market_agent.state import BatteryMarketState


def report_generation_agent(state: BatteryMarketState) -> dict:
    """
    보고서 생성 에이전트 노드.

    TODO:
    - 보고서 목차 및 양식 정의
    - state["company_report"]와 state["comparison_report"]를 컨텍스트로 LLM 호출
    - 최종 보고서를 state["final_report"]에 저장
    """
    raise NotImplementedError
