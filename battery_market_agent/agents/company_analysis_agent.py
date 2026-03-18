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

import re

from battery_market_agent.config import Settings, analysis_rate_limiter
from battery_market_agent.rag import BatteryRAG

_URL_RE = re.compile(r"https?://[^\s'\"\)\]>,<]+")
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
    model=_settings.analysis_model_name,
    api_key=_settings.openai_api_key,
    rate_limiter=analysis_rate_limiter,
    max_retries=6,
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
    "- 보고서 형식은 미정이므로 수집 정보를 구조화하여 전달하세요.\n\n"
    "균형 분석 원칙 (필수):\n"
    "- 긍정적 성과(수주·성장·기술 강점)와 부정적 측면(리스크·한계·약점)을 반드시 함께 서술하세요.\n"
    "- 부정적 측면 예시: 실적 악화·적자, 고객 이탈, 공급망 차질, 가동률 하락, 경쟁사 위협,\n"
    "  소송·리콜, 수익성 압박, 기술 격차, 원자재 의존도, 규제 리스크.\n"
    "- 긍정 정보만 강조하는 보고서는 불완전한 분석입니다. 부정적 사실도 동등하게 비중 있게 다루세요."
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

_RAG_COMMON_MAX_DOCS = 8   # 공통 문서 최대 수
_RAG_COMPANY_MAX_DOCS = 5  # 회사별 문서 최대 수
_RAG_MAX_CHARS = 1000      # 문서당 최대 문자 수

_COMPANY_RAG_QUERIES = {
    "LG에너지솔루션": [
        "LG에너지솔루션 배터리 기술 전략 NCM NCMA",
        "LG에너지솔루션 시장 점유율 북미 유럽",
    ],
    "CATL": [
        "CATL 배터리 기술 전략 LFP 각형",
        "CATL 시장 점유율 중국 글로벌",
    ],
}


def _format_section(title: str, docs: list, max_docs: int, offset: int = 0) -> tuple[list[str], int]:
    """문서 섹션을 포맷하고 (lines, 사용된_문서_수)를 반환한다."""
    used = docs[:max_docs]
    lines = [f"\n[{title}]"]
    for i, doc in enumerate(used, offset + 1):
        source = doc.metadata.get("source", "")
        page = doc.metadata.get("page", "")
        ref = f" ({source}, p.{page})" if source else ""
        content = doc.page_content.strip()[:_RAG_MAX_CHARS]
        print(f"  [문서 {i}{ref}] {len(content)}자 전달")
        lines.append(f"\n[문서 {i}{ref}]\n{content}")
    return lines, len(used)


def _format_rag_context(common_docs: list, company_docs: list) -> str:
    """공통 문서와 회사별 문서를 섹션 구분하여 supervisor 전달용 문자열로 포맷한다.

    company_docs에서 common_docs와 source+page가 겹치는 문서는 제외한다.
    """
    if not common_docs and not company_docs:
        print("[_format_rag_context] retrieved_docs 없음 — RAG 컨텍스트 미사용")
        return ""

    # 공통 문서 key set으로 회사별 중복 제거
    common_keys = {
        f"{d.metadata.get('source', '')}_{d.metadata.get('page', '')}"
        for d in common_docs
    }
    deduped_company_docs = [
        d for d in company_docs
        if f"{d.metadata.get('source', '')}_{d.metadata.get('page', '')}" not in common_keys
    ]

    print(f"[_format_rag_context] 공통 {len(common_docs)}개 중 최대 {_RAG_COMMON_MAX_DOCS}개, "
          f"회사별 {len(deduped_company_docs)}개 중 최대 {_RAG_COMPANY_MAX_DOCS}개 사용 "
          f"(중복 {len(company_docs) - len(deduped_company_docs)}개 제외, 문서당 최대 {_RAG_MAX_CHARS}자)")

    lines = ["[RAG 컨텍스트 — 사전 수집된 배터리 산업 배경 지식]"]

    section_lines, used_common = _format_section(
        "공통 — 배터리 시장 배경", common_docs, _RAG_COMMON_MAX_DOCS, offset=0
    )
    lines.extend(section_lines)

    if deduped_company_docs:
        section_lines, _ = _format_section(
            "회사별 — 기술·전략 문서", deduped_company_docs, _RAG_COMPANY_MAX_DOCS, offset=used_common
        )
        lines.extend(section_lines)

    return "\n".join(lines)


def _retrieve_company_docs(company: str) -> list:
    """회사별 특화 쿼리로 RAG를 검색하고 중복 제거된 문서 목록을 반환한다."""
    rag = BatteryRAG.get_instance(Settings())
    queries = _COMPANY_RAG_QUERIES.get(company, [f"{company} 배터리 기술 전략"])

    seen: set[str] = set()
    docs = []
    for query in queries:
        for doc in rag.retrieve(query, company=company):
            key = f"{doc.metadata.get('source', '')}_{doc.metadata.get('page', '')}"
            if key not in seen:
                seen.add(key)
                docs.append(doc)

    print(f"[company_analysis_agent] {company} 회사별 RAG 검색: {len(docs)}개 문서")
    return docs


def company_analysis_agent(state) -> dict:
    """
    기업 분석 Supervisor 노드.

    공통 retrieved_docs + 회사별 특화 RAG 검색 결과를 합쳐 supervisor에 전달하고,
    최종 메시지를 state["company_report"][company]에 저장한다.
    Rate Limit 에러 시 최대 3회 재시도(지수 백오프)한다.
    """
    import time
    from openai import RateLimitError

    company = state["company"]
    common_docs = state.get("retrieved_docs", [])
    company_docs = _retrieve_company_docs(company)
    rag_context = _format_rag_context(common_docs, company_docs)

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

    # supervisor 내부 메시지 전체에서 URL 수집 (market_analysis_agent 등의 ToolMessage 포함)
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for msg in result["messages"]:
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        for url in _URL_RE.findall(content):
            if url not in seen:
                seen.add(url)
                sources.append({"url": url, "title": "", "tool": getattr(msg, "name", "")})

    market_sources = state.get("market_sources", {})
    market_sources[company] = sources

    return {"company_report": company_report, "market_sources": market_sources}
