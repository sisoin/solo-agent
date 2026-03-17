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
from langchain_openai import ChatOpenAI
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
_llm = ChatOpenAI(
    model=_settings.model_name,
    api_key=_settings.openai_api_key,
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
    tools=[search_web],
    name="tech_analysis_agent",
    prompt=(
        "당신은 배터리 기술 역량 분석 전문 에이전트입니다.\n"
        "주어진 기업의 배터리 셀 기술, 양극재, BMS, 생산 공정을 분석하세요.\n\n"
        "RAG·웹서치 균형 활용 지침:\n"
        "- 메시지에 [RAG 컨텍스트]가 포함된 경우, 먼저 검토하여 이미 확보된 기술 정보를 파악하세요.\n"
        "- RAG에 있는 기술 사양·특허·공정 정보는 그대로 활용하세요.\n"
        "- 아래 항목은 RAG 유무와 관계없이 search_web으로 최신 정보를 보완하세요:\n"
        "  · 차세대 배터리(전고체·나트륨이온 등) 개발 최신 동향\n"
        "  · 최근 1년 이내 특허 출원·기술 발표\n"
        "  · 경쟁사 대비 기술 격차 관련 최신 보도\n"
        "- 낙관적 전망뿐 아니라 기술적 한계와 경쟁사 위협도 함께 조사하세요.\n"
        "- 분석 완료 후 구조화된 기술 분석 보고서를 반환하세요."
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
    "- 메시지에 포함된 [RAG 컨텍스트]는 사전 수집된 배터리 산업 배경 지식입니다.\n"
    "  각 에이전트에게 이 컨텍스트를 참고 자료로 전달하고, 웹서치로 최신 정보를 보완하도록 안내하세요.\n"
    "- RAG 컨텍스트만으로 충분한 항목은 웹서치를 생략해도 되지만,\n"
    "  최신성이 필요한 항목(시장 규모, 원자재 가격, 뉴스)은 반드시 웹서치로 보완하세요.\n"
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

_RAG_MAX_DOCS = 6        # 전달할 최대 문서 수
_RAG_MAX_CHARS = 400    # 문서당 최대 문자 수


def _format_rag_context(retrieved_docs) -> str:
    """retrieved_docs를 supervisor에 전달할 컨텍스트 문자열로 포맷한다.

    TPM 한도 초과 방지를 위해 상위 _RAG_MAX_DOCS개 문서만,
    각 문서는 _RAG_MAX_CHARS자로 잘라 전달한다.
    """
    if not retrieved_docs:
        print("[_format_rag_context] retrieved_docs 없음 — RAG 컨텍스트 미사용")
        return ""
    total = len(retrieved_docs)
    used = retrieved_docs[:_RAG_MAX_DOCS]
    print(f"[_format_rag_context] 전체 {total}개 중 {len(used)}개 사용 (문서당 최대 {_RAG_MAX_CHARS}자)")
    lines = ["[RAG 컨텍스트 — 사전 수집된 배터리 산업 배경 지식]"]
    for i, doc in enumerate(used, 1):
        source = doc.metadata.get("source", "")
        page = doc.metadata.get("page", "")
        ref = f" ({source}, p.{page})" if source else ""
        content = doc.page_content.strip()[:_RAG_MAX_CHARS]
        print(f"  [문서 {i}{ref}] {len(content)}자 전달")
        lines.append(f"\n[문서 {i}{ref}]\n{content}")
    return "\n".join(lines)


def company_analysis_agent(state) -> dict:
    """
    기업 분석 Supervisor 노드.

    retrieved_docs(RAG)를 요약 컨텍스트로 포함한 초기 메시지를 supervisor에 전달하고,
    최종 메시지를 state["company_report"][company]에 저장한다.
    Rate Limit 에러 시 최대 3회 재시도(지수 백오프)한다.
    """
    import time
    from openai import RateLimitError

    company = state["company"]
    rag_context = _format_rag_context(state.get("retrieved_docs", []))

    user_message = (
        f"{company}의 시장 동향, 기술 역량, SWOT 분석을 수행해주세요.\n\n"
        + rag_context
        if rag_context
        else f"{company}의 시장 동향, 기술 역량, SWOT 분석을 수행해주세요."
    )

    for attempt in range(3):
        try:
            result = company_supervisor.invoke({
                "messages": [("user", user_message)]
            })
            break
        except RateLimitError as e:
            if attempt == 2:
                raise
            wait = 30 * (attempt + 1)
            print(f"[company_analysis_agent] Rate limit 초과, {wait}초 후 재시도... ({attempt+1}/3)")
            time.sleep(wait)

    company_report = state.get("company_report", {})
    company_report[company] = result["messages"][-1].content

    return {"company_report": company_report}
