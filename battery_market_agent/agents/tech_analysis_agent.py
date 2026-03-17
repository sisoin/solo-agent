"""
기술 분석 에이전트

역할:
    벡터 저장소에 인덱싱된 기업 기술 PDF 문서를 RAG로 검색하여
    LG에너지솔루션·CATL의 기술 역량을 분석한다.

RAG 구조:
    data/tech_docs/
        ├── LG에너지솔루션/   ← 기술 PDF (특허, 기술보고서 등)
        └── CATL/             ← 기술 PDF (특허, 기술보고서 등)

    BatteryRAG.retrieve(query, company=state["company"])로
    해당 회사 문서만 필터링하여 검색한다.

입력:
    state["company"]       : 분석 대상 회사명
    state["tech_queries"]  : RAG 검색 쿼리 목록 (비어 있으면 기본값 사용)

출력:
    state["retrieved_docs"]: 쿼리별 RAG 검색 결과 (누적)
    state["tech_analysis"] : 최종 기술 역량 분석 보고서
"""
from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document

from battery_market_agent.config import Settings
from battery_market_agent.rag import BatteryRAG
from battery_market_agent.state import TechAnalysisState

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

_settings = Settings()
_llm = ChatAnthropic(
    model=_settings.model_name,
    api_key=_settings.anthropic_api_key,
)

# 기본 기술 분석 쿼리 — tech_queries가 비어 있을 때 사용
DEFAULT_TECH_QUERIES = [
    "배터리 셀 기술 에너지 밀도 용량",
    "양극재 기술 NCM LFP NCMA",
    "음극재 기술 실리콘 흑연",
    "BMS 배터리 관리 시스템",
    "생산 공정 제조 기술 원가",
    "차세대 배터리 전고체 기술 개발",
]

SYSTEM_PROMPT = """당신은 배터리 기술 전문 분석가입니다.
제공된 기술 문서를 바탕으로 해당 기업의 기술 역량을 분석하세요.

분석 항목:
1. 배터리 셀 기술 및 에너지 밀도
2. 양극재·음극재 기술 수준
3. BMS(배터리 관리 시스템) 역량
4. 생산 공정 및 원가 경쟁력
5. 차세대 기술(전고체 등) 개발 현황
6. 핵심 특허 및 기술 차별화 요소

지침:
- 제공된 문서 내용에 근거하여 분석하세요.
- 각 항목을 구체적 근거와 함께 서술하세요.
- 최종 답변은 항목별로 구조화된 한국어 분석 보고서 형식으로 작성하세요.
"""

# ---------------------------------------------------------------------------
# 노드
# ---------------------------------------------------------------------------

def tech_analysis_agent(state: TechAnalysisState) -> dict:
    """
    기술 분석 에이전트 노드.

    1. tech_queries(없으면 기본값)로 BatteryRAG에서 회사별 문서 검색
    2. 검색된 문서를 컨텍스트로 LLM 기술 분석 수행
    """
    company = state["company"]
    queries = state.get("tech_queries") or DEFAULT_TECH_QUERIES

    rag = BatteryRAG.get_instance(_settings)

    # 쿼리별 문서 검색 (회사 필터 적용)
    all_docs: list[Document] = []
    for query in queries:
        docs = rag.retrieve(query, company=company)
        all_docs.extend(docs)

    # 중복 제거 (source + page 기준)
    seen: set[str] = set()
    unique_docs: list[Document] = []
    for doc in all_docs:
        key = f"{doc.metadata.get('source', '')}_{doc.metadata.get('page', '')}"
        if key not in seen:
            seen.add(key)
            unique_docs.append(doc)

    # 문서를 컨텍스트 문자열로 변환
    context_parts = []
    for i, doc in enumerate(unique_docs, 1):
        source = doc.metadata.get("filename", doc.metadata.get("source", "알 수 없음"))
        page = doc.metadata.get("page", "")
        header = f"[문서 {i}] {source}" + (f" (p.{page})" if page else "")
        context_parts.append(f"{header}\n{doc.page_content.strip()}")
    context = "\n\n---\n\n".join(context_parts) if context_parts else "검색된 문서가 없습니다."

    # LLM 기술 분석
    user_message = f"""다음은 '{company}'의 기술 관련 문서입니다.

{context}

위 문서를 바탕으로 '{company}'의 기술 역량을 분석 항목에 따라 분석해주세요."""

    response = _llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("user", user_message),
    ])

    return {
        "retrieved_docs": unique_docs,
        "tech_analysis": response.content,
    }
