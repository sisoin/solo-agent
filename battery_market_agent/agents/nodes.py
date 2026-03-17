"""
LangGraph 노드 함수 모음.

각 노드는 BatteryMarketState를 받아 부분 상태 업데이트(dict)를 반환합니다.

노드 역할:
- retrieve_node  : 현재 쿼리 기반 RAG 검색
- analyze_node   : LLM 기반 시장 전략 분석
- tool_node      : 에이전트가 요청한 도구 실행
- summarize_node : 최종 구조화 보고서 생성
"""
from battery_market_agent.state import BatteryMarketState


def retrieve_node(state: BatteryMarketState) -> dict:
    """TODO: BatteryRAG.retrieve() 호출 후 retrieved_docs로 상태 업데이트."""
    raise NotImplementedError


def analyze_node(state: BatteryMarketState) -> dict:
    """TODO: 도구 및 검색 컨텍스트를 활용한 LLM 에이전트 실행."""
    raise NotImplementedError


def tool_node(state: BatteryMarketState) -> dict:
    """TODO: 에이전트 메시지의 도구 호출을 실행하고 결과 반환."""
    raise NotImplementedError


def summarize_node(state: BatteryMarketState) -> dict:
    """TODO: 분석 결과를 최종 전략 보고서로 종합."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 라우팅
# ---------------------------------------------------------------------------

def route_after_analyze(state: BatteryMarketState) -> str:
    """TODO: 다음 노드 이름 반환 — 'tool_node', 'summarize_node', 또는 END."""
    raise NotImplementedError
