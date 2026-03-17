"""
배터리 시장 전략 에이전트의 LangGraph 그래프 정의.

그래프 흐름:
    retrieve_node → analyze_node → (tool_node →)* summarize_node → END
"""
from langgraph.graph import StateGraph, END

from battery_market_agent.state import BatteryMarketState
from battery_market_agent.agents.nodes import (
    retrieve_node,
    analyze_node,
    tool_node,
    summarize_node,
    route_after_analyze,
)


def build_graph():
    """LangGraph 상태 머신을 빌드하고 컴파일합니다."""
    # TODO: BatteryMarketState 플레이스홀더를 실제 TypedDict로 교체
    graph = StateGraph(BatteryMarketState)

    # ── 노드 ───────────────────────────────────────────────────────────────
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("tools", tool_node)
    graph.add_node("summarize", summarize_node)

    # ── 엣지 ───────────────────────────────────────────────────────────────
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_conditional_edges(
        "analyze",
        route_after_analyze,
        {
            "tools": "tools",
            "summarize": "summarize",
        },
    )
    graph.add_edge("tools", "analyze")   # 도구 결과를 에이전트로 루프백
    graph.add_edge("summarize", END)

    return graph.compile()
