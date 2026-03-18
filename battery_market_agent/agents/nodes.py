"""
LangGraph 노드 함수 모음.

각 노드는 BatteryMarketState를 받아 부분 상태 업데이트(dict)를 반환합니다.

노드 역할:
- retrieve_node : 배터리 시장 공통 배경 문서를 RAG로 선검색하여 하위 에이전트에 전달
"""
from langchain_core.documents import Document

from battery_market_agent.config import Settings
from battery_market_agent.rag import BatteryRAG
from battery_market_agent.state import BatteryMarketState


DEFAULT_RETRIEVE_QUERIES = [
    "배터리 시장 규모 성장률 전망",
    "전기차 배터리 수요 지역별 동향",
    "리튬 코발트 니켈 원자재 가격",
    "배터리 산업 규제 정책",
    "LG에너지솔루션 CATL 시장 점유율 경쟁",
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

    # 문서별 출처를 source 기준 중복 제거하여 rag_sources로 추출
    source_seen: set[str] = set()
    rag_sources: list[dict] = []
    for doc in unique_docs:
        source = doc.metadata.get("source", "")
        if source and source not in source_seen:
            source_seen.add(source)
            rag_sources.append({
                "source":   source,
                "company":  doc.metadata.get("company", ""),
                "filename": doc.metadata.get("filename", ""),
            })

    return {"retrieved_docs": unique_docs, "rag_sources": rag_sources}
