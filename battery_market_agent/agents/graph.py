"""
배터리 시장 전략 에이전트의 LangGraph 그래프 정의.

그래프 흐름:
    retrieve
        ↓
    branch_companies (Send API)
        ├── analyze_company [LG에너지솔루션]  ─┐
        └── analyze_company [CATL]            ─┴─→ compare → summarize → END
"""
from langgraph.graph import StateGraph, END

from battery_market_agent.state import BatteryMarketState
from battery_market_agent.agents.nodes import (
    retrieve_node,
    analyze_company_node,
    compare_node,
    summarize_node,
    branch_companies,
    route_after_compare,
)


def build_graph():
    """LangGraph 상태 머신을 빌드하고 컴파일합니다."""
    # TODO: BatteryMarketState 플레이스홀더를 실제 TypedDict로 교체
    graph = StateGraph(BatteryMarketState)

    # ── 노드 ───────────────────────────────────────────────────────────────
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("analyze_company", analyze_company_node)
    graph.add_node("compare", compare_node)
    graph.add_node("summarize", summarize_node)

    # ── 엣지 ───────────────────────────────────────────────────────────────
    graph.set_entry_point("retrieve")

    # retrieve → branch_companies (Send) → analyze_company (병렬)
    graph.add_conditional_edges("retrieve", branch_companies, ["analyze_company"])

    # analyze_company 두 개 모두 완료 → compare (자동 합류)
    graph.add_edge("analyze_company", "compare")

    # compare → summarize 또는 END
    graph.add_conditional_edges(
        "compare",
        route_after_compare,
        {
            "summarize": "summarize",
        },
    )
    graph.add_edge("summarize", END)

    return graph.compile()
