"""
기업 분석 Supervisor (langgraph_supervisor.create_supervisor 기반)

Supervisor LLM이 세 하위 에이전트를 순차적으로 조율하며
각 에이전트가 완료되면 결과를 다시 Supervisor에게 반환(핸드오프)한다.

LG에너지솔루션 / CATL은 상위 그래프의 Send API로 병렬 처리되고
각 회사 내 에이전트 조율은 Supervisor LLM이 담당한다.

실행 흐름:
    supervisor (LLM)
        ↓ transfer_to_market_analysis_agent
    market_analysis_agent  →  결과 반환
        ↓ transfer_back_to_supervisor
    supervisor (LLM)
        ↓ transfer_to_tech_analysis_agent
    tech_analysis_agent    →  결과 반환
        ↓ transfer_back_to_supervisor
    supervisor (LLM)
        ↓ transfer_to_swot_analysis_agent
    swot_analysis_agent    →  결과 반환
        ↓ transfer_back_to_supervisor
    supervisor (LLM) — 세 결과 종합 후 종료
"""
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from battery_market_agent.config import Settings
from battery_market_agent.tools import (
    search_web,
    fetch_google_news,
    fetch_price_trends,
    search_battery_market_data,
    summarize_regulations,
    read_pdf,
)
from battery_market_agent.agents.market_analysis_agent import _agent as market_agent_graph
from battery_market_agent.agents.swot import swot_subgraph
from battery_market_agent.agents.swot_analysis_agent import (
    STRENGTH_CRITERIA,
    WEAKNESS_CRITERIA,
    OPPORTUNITY_CRITERIA,
    THREAT_CRITERIA,
)

_settings = Settings()
_llm = ChatAnthropic(
    model=_settings.model_name,
    api_key=_settings.anthropic_api_key,
)

# ---------------------------------------------------------------------------
# SWOT 서브그래프를 Tool로 래핑 (swot_analysis_agent에서 사용)
# ---------------------------------------------------------------------------

@tool
def run_swot_analysis(company: str) -> str:
    """SWOT 분석 서브그래프를 실행하여 2×2 SWOT 행렬 문자열을 반환합니다."""
    result = swot_subgraph.invoke({
        "subject":  company,
        "raw_info": [],
        "criteria": {
            "strength":    STRENGTH_CRITERIA,
            "weakness":    WEAKNESS_CRITERIA,
            "opportunity": OPPORTUNITY_CRITERIA,
            "threat":      THREAT_CRITERIA,
        },
    })
    return result["swot_matrix"]


# ---------------------------------------------------------------------------
# 하위 에이전트 (create_react_agent + name)
# name은 create_supervisor가 transfer_to_{name} 핸드오프 도구를 자동 생성할 때 사용
# ---------------------------------------------------------------------------

# 시장 분석: market_analysis_agent.py에서 컴파일된 그래프를 재사용
_market_agent = market_agent_graph   # name="market_analysis_agent" 이미 설정됨

# 기술 분석
_tech_agent = create_react_agent(
    model=_llm,
    tools=[read_pdf, search_web],
    name="tech_analysis_agent",
    prompt=(
        "당신은 배터리 기술 역량 분석 전문 에이전트입니다.\n"
        "주어진 기업의 배터리 셀 기술, 양극재, BMS, 생산 공정을 분석하세요.\n"
        "TODO: RAG 검색 도구 추가 후 기업 기술 PDF 문서를 우선 참조하세요.\n"
        "분석 완료 후 구조화된 기술 분석 보고서를 반환하세요."
    ),
)

# SWOT 분석
_swot_agent = create_react_agent(
    model=_llm,
    tools=[run_swot_analysis, search_web, fetch_google_news],
    name="swot_analysis_agent",
    prompt=(
        "당신은 SWOT 분석 전문 에이전트입니다.\n"
        "run_swot_analysis 도구로 SWOT 분석을 실행하고 결과를 반환하세요.\n"
        "추가 맥락이 필요하면 search_web, fetch_google_news를 활용하세요."
    ),
)

# ---------------------------------------------------------------------------
# Supervisor
# ---------------------------------------------------------------------------

_SUPERVISOR_PROMPT = (
    "당신은 단일 기업의 종합 분석을 조율하는 Supervisor입니다.\n\n"
    "담당 에이전트:\n"
    "1. market_analysis_agent : 시장 동향 수집 (규모, 성장률, 수요, 원자재 가격)\n"
    "2. tech_analysis_agent   : 기술 역량 분석 (셀 기술, 양극재, BMS, 생산 공정)\n"
    "3. swot_analysis_agent   : SWOT 분석 수행 및 2×2 행렬 생성\n\n"
    "지침:\n"
    "- 세 에이전트를 순서대로 호출하여 각 분석을 완료하세요.\n"
    "- 모든 에이전트 결과를 수집한 뒤 종합 기업 보고서를 작성하세요.\n"
    "- 보고서 형식은 미정이므로 수집 정보를 구조화하여 전달하세요."
)

company_supervisor = create_supervisor(
    model=_llm,
    agents=[_market_agent, _tech_agent, _swot_agent],
    system_prompt=_SUPERVISOR_PROMPT,
    add_handoff_back_messages=True,   # 에이전트 → Supervisor 복귀 메시지 추가
    output_mode="last_message",       # 최종 Supervisor 메시지만 반환
).compile()

# ---------------------------------------------------------------------------
# 메인 그래프 노드 래퍼
# ---------------------------------------------------------------------------

def company_analysis_agent(state) -> dict:
    """
    기업 분석 Supervisor 노드.

    company_supervisor를 호출하고 최종 메시지를
    state["company_report"][company]에 저장한다.
    """
    company = state["company"]

    result = company_supervisor.invoke({
        "messages": [
            ("user", f"{company}의 시장 동향, 기술 역량, SWOT 분석을 수행해주세요.")
        ]
    })

    company_report = state.get("company_report", {})
    company_report[company] = result["messages"][-1].content

    return {"company_report": company_report}
