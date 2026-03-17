"""
SWOT 분석 에이전트

역할:
    시장 분석 에이전트(market_analysis_agent)가 수집한 기업 정보를
    SWOT 서브그래프(swot_subgraph)에 전달하여 분석을 수행하고
    결과를 state["swot_table"]에 저장한다.

입력:
    state["company"]      : 분석 대상 회사명
    state["market_trends"]: 시장 분석 에이전트 결과

출력:
    state["swot_table"]: 회사별 SWOT 마크다운 표 문자열
"""
from battery_market_agent.state import BatteryMarketState
from battery_market_agent.agents.swot import swot_subgraph

# ---------------------------------------------------------------------------
# 평가 기준 (나중에 채울 것)
# ---------------------------------------------------------------------------

STRENGTH_CRITERIA = ""       # 강점 판단 기준
WEAKNESS_CRITERIA = ""       # 약점 판단 기준
OPPORTUNITY_CRITERIA = ""    # 기회 판단 기준
THREAT_CRITERIA = ""         # 위협 판단 기준

# ---------------------------------------------------------------------------
# 노드
# ---------------------------------------------------------------------------

def swot_analysis_agent(state: BatteryMarketState) -> dict:
    """
    SWOT 분석 에이전트 노드.

    market_trends를 raw_info로 swot_subgraph에 전달하고,
    반환된 swot_matrix를 state["swot_table"]에 저장한다.
    """
    company = state["company"]
    market_trends = state.get("market_trends", {}).get(company, "")

    result = swot_subgraph.invoke({
        "subject": company,
        "raw_info": [market_trends],
        "criteria": {
            "strength":    STRENGTH_CRITERIA,
            "weakness":    WEAKNESS_CRITERIA,
            "opportunity": OPPORTUNITY_CRITERIA,
            "threat":      THREAT_CRITERIA,
        },
    })

    swot_table = state.get("swot_table", {})
    swot_table[company] = result["swot_matrix"]

    return {"swot_table": swot_table}
