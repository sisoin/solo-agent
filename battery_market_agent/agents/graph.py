"""
배터리 시장 전략 에이전트의 LangGraph 그래프 정의.

그래프 흐름:
    START
      ↓
    retrieve
      ↓
    branch_companies (Send API — 회사별 병렬 분기)
      ├── [LG에너지솔루션]                      ├── [CATL]
      │   market_analysis_agent                 │   market_analysis_agent
      │   tech_analysis_agent     (병렬)        │   tech_analysis_agent     (병렬)
      │   swot_analysis_agent                   │   swot_analysis_agent
      │        ↓                                │        ↓
      │   company_analysis_agent (supervisor)   │   company_analysis_agent (supervisor)
      └────────────────────┬────────────────────┘
                           ↓  (양쪽 완료 후 자동 합류)
                  company_comparison_agent
                           ↓
                  report_generation_agent
                           ↓
                          END

NOTE:
    - 각 회사 내 market / tech / swot 실행 순서는 company_analysis_agent(supervisor)가 결정
    - company_comparison_agent 이후 workflow 미정
"""
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from battery_market_agent.state import BatteryMarketState
from battery_market_agent.agents.nodes import retrieve_node
from battery_market_agent.agents.company_analysis_agent import company_analysis_agent
from battery_market_agent.agents.company_comparison_agent import company_comparison_agent
from battery_market_agent.agents.report_generation_agent import report_generation_agent

COMPANIES = ["LG에너지솔루션", "CATL"]


def branch_companies(state: BatteryMarketState) -> list[Send]:
    """LG에너지솔루션 / CATL을 company_analysis_agent에 병렬 분기."""
    return [
        Send("company_analysis", {**state, "company": company})
        for company in COMPANIES
    ]


def build_graph():
    """LangGraph 상태 머신을 빌드하고 컴파일합니다."""
    # TODO: BatteryMarketState 플레이스홀더를 실제 TypedDict로 교체
    graph = StateGraph(BatteryMarketState)

    # ── 노드 ────────────────────────────────────────────────────────────────
    graph.add_node("retrieve",            retrieve_node)
    graph.add_node("company_analysis",    company_analysis_agent)    # 회사별 supervisor 노드
    graph.add_node("company_comparison",  company_comparison_agent)  # 두 결과 합류
    graph.add_node("report_generation",   report_generation_agent)

    # ── 엣지 ────────────────────────────────────────────────────────────────
    graph.set_entry_point("retrieve")

    # retrieve → branch_companies(Send) → company_analysis ×2 (병렬)
    graph.add_conditional_edges("retrieve", branch_companies, ["company_analysis"])

    # LG / CATL company_analysis 둘 다 완료 → company_comparison (자동 합류)
    graph.add_edge("company_analysis",   "company_comparison")
    graph.add_edge("company_comparison", "report_generation")
    graph.add_edge("report_generation",  END)

    return graph.compile()
