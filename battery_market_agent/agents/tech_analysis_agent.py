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
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from battery_market_agent.config import Settings, analysis_rate_limiter
from battery_market_agent.rag import BatteryRAG
from battery_market_agent.state import TechAnalysisState

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

_settings = Settings()
_llm = ChatOpenAI(
    model=_settings.analysis_model_name,
    api_key=_settings.openai_api_key,
    rate_limiter=analysis_rate_limiter,
    max_retries=6,
)

# ---------------------------------------------------------------------------
# 기술 분석 평가 기준
# 각 분석 항목에서 LLM이 확인해야 할 구체적 평가 포인트.
# SYSTEM_PROMPT에 주입되어 분석 깊이와 일관성을 높인다.
# ---------------------------------------------------------------------------

TECH_CRITERIA = {
    "cell": (
        "셀 에너지 밀도(Wh/kg·Wh/L) 수치 및 경쟁사 대비 수준, "
        "사이클 수명(80% 용량 유지 기준 충방전 횟수), "
        "급속 충전 C-rate 및 충전 시간, "
        "열폭주 방지 기술 및 안전성 인증, "
        "NCM·LFP·NCMA·나트륨이온 등 화학 계열 포트폴리오 다양성"
    ),
    "materials": (
        "양극재 니켈 함량(고니켈 NCM 9xx·NCMA) 및 자체 개발·내재화 여부, "
        "음극재 실리콘 적용 비율(Si 함량 %) 및 팽창 제어 기술 수준, "
        "양극재·음극재 외부 조달 의존도 및 공급망 리스크, "
        "전해질(액체·고체·반고체) 기술 개발 현황"
    ),
    "bms": (
        "SOC(충전 상태)·SOH(건강 상태) 추정 정확도, "
        "AI·머신러닝 기반 BMS 적용 여부, "
        "OTA(무선) 업데이트 지원 여부, "
        "셀 밸런싱 기술 수준 및 배터리 팩 통합 관리 능력"
    ),
    "manufacturing": (
        "셀 제조 원가($/kWh) 및 경쟁사 대비 수준, "
        "생산 수율(%) 및 불량률, "
        "건식 전극(Dry Electrode) 공정 등 차세대 제조 기술 도입 여부, "
        "스마트팩토리·자동화 수준, "
        "GWh당 투자비(CAPEX 효율성)"
    ),
    "next_gen": (
        "전고체 배터리 개발 단계(연구·시제품·파일럿·양산 로드맵), "
        "4680(원통형 대형 셀) 등 폼팩터 혁신 현황, "
        "리튬메탈 음극 기술 개발 수준, "
        "상용화 예정 시기 및 실현 가능성 평가, "
        "공식 발표 일정 대비 실제 진행 현황 괴리"
    ),
    "patent": (
        "보유 특허 총 수 및 핵심 기술 영역별 분포, "
        "소재·셀·BMS·제조공정 각 분야 핵심 특허 보유 여부, "
        "기술 라이선스 수입·지출 현황, "
        "특허 분쟁·소송 이력 및 경쟁사 특허 회피 설계 능력"
    ),
}

# RAG 검색 쿼리 — TECH_CRITERIA 항목과 1:1 대응
DEFAULT_TECH_QUERIES = [
    "배터리 셀 에너지 밀도 Wh/kg 사이클 수명 안전성",
    "양극재 NCM NCMA 고니켈 음극재 실리콘 내재화",
    "BMS 배터리 관리 시스템 SOC SOH AI",
    "배터리 제조 원가 $/kWh 수율 건식 전극 스마트팩토리",
    "전고체 배터리 차세대 기술 개발 로드맵 상용화",
    "배터리 특허 핵심 기술 라이선스 소송",
]

SYSTEM_PROMPT = """당신은 배터리 기술 전문 분석가입니다.
제공된 기술 문서를 바탕으로 해당 기업의 기술 역량을 분석하세요.

분석 항목 및 평가 기준:

1. 배터리 셀 기술 및 에너지 밀도
   평가 기준: {cell}

2. 양극재·음극재 기술 수준
   평가 기준: {materials}

3. BMS(배터리 관리 시스템) 역량
   평가 기준: {bms}

4. 생산 공정 및 원가 경쟁력
   평가 기준: {manufacturing}

5. 차세대 기술(전고체 등) 개발 현황
   평가 기준: {next_gen}

6. 핵심 특허 및 기술 차별화 요소
   평가 기준: {patent}

균형 잡힌 분석 지침:
- 각 항목에서 기술적 강점뿐 아니라 한계와 과제도 명시하세요.
- 경쟁사 대비 뒤처지는 영역, 아직 상용화되지 않은 기술, 양산 수율 문제 등 부정적 측면을 누락하지 마세요.
- 공식 발표·특허 자료의 낙관적 수치와 실제 양산 성과 사이의 괴리가 있다면 명시하세요.
- 제공된 문서 내용에 근거하여 분석하세요.
- 각 항목을 구체적 근거와 함께 서술하세요.
- 최종 답변은 항목별로 구조화된 한국어 분석 보고서 형식으로 작성하세요.
""".format(**TECH_CRITERIA)

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
