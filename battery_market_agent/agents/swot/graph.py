"""
SWOT 분석 서브그래프.

흐름:
    gather_info → classify_swot → format_matrix → END

외부에서 사용:
    from battery_market_agent.agents.swot import swot_subgraph

    result = swot_subgraph.invoke({"subject": "삼성SDI", "raw_info": []})
    print(result["swot_matrix"])
"""
from langgraph.graph import StateGraph, END

from .state import SWOTState
from .nodes import gather_info_node, classify_swot_node, format_matrix_node


def build_swot_subgraph():
    graph = StateGraph(SWOTState)

    # ── 노드 ────────────────────────────────────────────────────────────────
    graph.add_node("gather_info",    gather_info_node)
    graph.add_node("classify_swot",  classify_swot_node)
    graph.add_node("format_matrix",  format_matrix_node)

    # ── 엣지 ────────────────────────────────────────────────────────────────
    graph.set_entry_point("gather_info")
    graph.add_edge("gather_info",   "classify_swot")
    graph.add_edge("classify_swot", "format_matrix")
    graph.add_edge("format_matrix", END)

    return graph.compile()


swot_subgraph = build_swot_subgraph()
