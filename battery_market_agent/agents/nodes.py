"""
LangGraph 노드 함수 모음.

각 노드는 BatteryMarketState를 받아 부분 상태 업데이트(dict)를 반환합니다.

노드 역할:
- retrieve_node       : 현재 쿼리 기반 RAG 검색
- branch_companies    : LG에너지솔루션 / CATL 병렬 분기 (Send API)
- analyze_company_node: 회사별 LLM 분석 (병렬 실행)
- compare_node        : 두 분석 결과 비교 및 종합
- summarize_node      : 최종 구조화 보고서 생성
"""
from langchain_core.documents import Document
from langgraph.types import Send

from battery_market_agent.config import Settings
from battery_market_agent.rag import BatteryRAG
from battery_market_agent.state import BatteryMarketState
from battery_market_agent.agents.market_analysis_agent import market_analysis_agent
from battery_market_agent.agents.swot_analysis_agent import swot_analysis_agent
from battery_market_agent.tools import (
    search_battery_market_data,
    analyze_competitors,
    fetch_price_trends,
    summarize_regulations,
    fetch_google_news,
    search_web,
    read_pdf,
)

COMPANIES = ["LG에너지솔루션", "CATL"]

DEFAULT_RETRIEVE_QUERIES = [
    "배터리 시장 규모 성장률 전망",
    "전기차 배터리 수요 지역별 동향",
    "리튬 코발트 니켈 원자재 가격",
    "배터리 산업 규제 정책",
    "LG에너지솔루션 CATL 시장 점유율 경쟁",
]

COMPANY_TOOLS = [
    search_battery_market_data,
    fetch_price_trends,
    summarize_regulations,
    fetch_google_news,
    search_web,
    read_pdf,
]


# ---------------------------------------------------------------------------
# 노드
# ---------------------------------------------------------------------------

def retrieve_node(state: BatteryMarketState) -> dict:
    """
    공통 RAG 검색 노드.

    branch_companies(Send) 전에 한 번 실행되어 배터리 시장 관련
    공통 문서를 검색하고 retrieved_docs에 저장한다.
    이후 각 company_analysis_agent에 그대로 전달된다.
    """
    rag = BatteryRAG.get_instance(Settings())

    all_docs: list[Document] = []
    for query in DEFAULT_RETRIEVE_QUERIES:
        docs = rag.retrieve(query)
        all_docs.extend(docs)

    # source + page 기준 중복 제거
    seen: set[str] = set()
    unique_docs: list[Document] = []
    for doc in all_docs:
        key = f"{doc.metadata.get('source', '')}_{doc.metadata.get('page', '')}"
        if key not in seen:
            seen.add(key)
            unique_docs.append(doc)

    print(f"[retrieve_node] RAG 검색 완료: 총 {len(unique_docs)}개 문서 (쿼리 {len(DEFAULT_RETRIEVE_QUERIES)}개)")
    for i, doc in enumerate(unique_docs, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "")
        chars = len(doc.page_content)
        print(f"  [{i}] {source} p.{page} ({chars}자)")

    return {"retrieved_docs": unique_docs}


def analyze_company_node(state: BatteryMarketState) -> dict:
    """
    단일 회사에 대한 LLM 분석 노드 (LG에너지솔루션 / CATL 각각 병렬 실행).

    state["company"]로 대상 회사를 식별하고,
    COMPANY_TOOLS를 활용해 시장 데이터·뉴스·가격 추이·규제를 수집·분석한다.

    실행 순서:
    1. market_analysis_agent  : 웹 서치로 시장 동향 수집
    2. swot_analysis_agent    : 수집 정보 기반 SWOT 분석 및 표 생성

    TODO:
    - market_analysis_agent(state) 호출 → state 업데이트
    - swot_analysis_agent(state) 호출 → state 업데이트
    - 결과를 state["company_analyses"][company]에 저장
    """
    raise NotImplementedError


def compare_node(state: BatteryMarketState) -> dict:
    """
    LG에너지솔루션 vs CATL 비교 분석 노드.

    두 analyze_company_node 결과가 모두 완료된 후 실행된다.

    TODO:
    - state["company_analyses"]["LG에너지솔루션"]
    - state["company_analyses"]["CATL"]
    위 두 결과를 바탕으로 LLM이 비교 분석 수행
    (시장점유율, 기술 전략, 원가 구조, 지역별 포지셔닝 등)
    """
    raise NotImplementedError


def summarize_node(state: BatteryMarketState) -> dict:
    """TODO: 비교 분석 결과를 최종 전략 보고서로 종합."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 라우팅
# ---------------------------------------------------------------------------

def branch_companies(state: BatteryMarketState) -> list[Send]:
    """
    LG에너지솔루션과 CATL을 병렬로 analyze_company_node에 분기한다.

    각 Send는 독립적인 state 슬라이스(company 필드 포함)를 전달하므로
    두 노드가 동시에 실행된다.
    """
    return [
        Send("analyze_company", {**state, "company": company})
        for company in COMPANIES
    ]


def route_after_compare(state: BatteryMarketState) -> str:
    """TODO: 비교 완료 후 다음 노드 반환 — 'summarize' 또는 END."""
    raise NotImplementedError
