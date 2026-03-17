# 프로젝트 구조 (Project Structure)

## 디렉토리 구조

```
solo-agent/
├── battery_market_agent/           # 메인 패키지
│   ├── main.py                     # 진입점 (entry point)
│   ├── agents/                     # 에이전트 구현체
│   │   ├── graph.py                # 최상위 LangGraph 정의
│   │   ├── nodes.py                # 노드 함수 (retrieve_node 등)
│   │   ├── market_analysis_agent.py
│   │   ├── tech_analysis_agent.py
│   │   ├── swot_analysis_agent.py
│   │   ├── company_analysis_agent.py
│   │   ├── company_comparison_agent.py
│   │   ├── report_generation_agent.py
│   │   ├── market/                 # Market 에이전트 전용 state
│   │   │   └── state.py
│   │   └── swot/                   # SWOT 서브그래프
│   │       ├── state.py
│   │       ├── nodes.py
│   │       └── graph.py
│   ├── config/
│   │   └── settings.py             # Pydantic Settings (환경변수 관리)
│   ├── state/                      # 공유 State 정의
│   │   ├── graph_state.py          # BatteryMarketState (최상위)
│   │   ├── company_analysis_state.py
│   │   ├── company_comparison_state.py
│   │   ├── report_state.py
│   │   └── tech_analysis_state.py
│   ├── rag/                        # RAG 구현
│   │   ├── retriever.py            # BatteryRAG 싱글턴
│   │   └── ingest.py               # 문서 인덱싱
│   ├── tools/                      # 에이전트 도구
│   │   ├── search_tools.py         # 웹 검색, 뉴스, PDF 읽기
│   │   ├── market_tools.py         # 시장 분석 도구 (TODO)
│   │   └── analysis_tools.py       # SWOT 매트릭스 렌더링
│   └── data/
│       └── tech_docs/
│           ├── LG에너지솔루션/     # LG 기술 문서 (PDF)
│           └── CATL/               # CATL 기술 문서 (PDF)
├── docs/                           # 문서
└── pyproject.toml                  # 의존성 관리
```

## 에이전트 구성

### 최상위 그래프 (`agents/graph.py`)

최상위 오케스트레이션 레이어. LangGraph `Send` API로 LG와 CATL 분석을 병렬 실행한다.

| 노드 | 역할 | 상태 |
|------|------|------|
| `retrieve_node` | 공통 RAG 검색 | ❌ TODO |
| `company_analysis_agent` | 단일 기업 분석 (Supervisor) | ✅ |
| `company_comparison_agent` | 기업 간 비교 분석 | ❌ TODO |
| `report_generation_agent` | 최종 보고서 생성 | ✅ |

### 에이전트별 역할

| 에이전트 | 패턴 | 입력 | 출력 |
|---------|------|------|------|
| `market_analysis_agent` | ReAct | `company` | `market_trends[company]` |
| `tech_analysis_agent` | RAG + LLM | `company`, `tech_queries` | `tech_analysis` |
| `swot_analysis_agent` | Subgraph | `company`, `market_trends` | `swot_table[company]` |
| `company_analysis_agent` | Supervisor | `company` | `company_report[company]` |
| `company_comparison_agent` | LLM | `company_report` x2 | `comparison_report` |
| `report_generation_agent` | Subgraph | `company_report`, `comparison_report` | `final_report`, 파일 경로 |

## State 계층 구조

```
BatteryMarketState (최상위)
├── retrieved_docs: list[Document]         ← retrieve_node 공통 RAG 결과
├── company_report: dict[str, str]         ← 기업별 분석 보고서
│   ├── "LG에너지솔루션" ← CompanyAnalysisState 출력
│   └── "CATL"           ← CompanyAnalysisState 출력
├── comparison_report: str                 ← company_comparison_agent 출력
└── final_report: str                      ← report_generation_agent 출력

CompanyAnalysisState (기업 분석, Supervisor 관리)
├── company: str
├── messages: list[AnyMessage]
├── market_analysis: str                   ← market_analysis_agent 출력
├── tech_analysis: str                     ← tech_analysis_agent 출력
├── swot_matrix: str                       ← swot_analysis_agent 출력
└── company_report: str                    ← Supervisor 종합 출력

SWOTState (SWOT 서브그래프 내부)
├── subject: str
├── raw_info: list[str]
├── strengths / weaknesses / opportunities / threats: list[str]
└── swot_matrix: str

ReportState (보고서 생성 서브그래프 내부)
├── company_report: dict[str, str]
├── comparison_report: str
├── sections: ReportSections | None        ← LLM 구조화 출력 중간값
├── final_report: str
├── report_md_path: str
└── report_pdf_path: str
```

## RAG 아키텍처

```
PDF 문서 (data/tech_docs/)
        ↓  PDFPlumberLoader
텍스트 청크 (chunk_size=1500, overlap=200)
        ↓  HuggingFaceEmbeddings (BAAI/bge-m3)
1024차원 벡터
        ↓  QdrantVectorStore (cosine similarity)
retrieve(query, company) → list[Document]
```

## 설정 구조 (`config/settings.py`)

```python
class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str
    model_name: str = "claude-sonnet-4-6"

    # RAG
    embedding_model: str = "BAAI/bge-m3"
    chunk_size: int = 1500
    chunk_overlap: int = 200
    retriever_k: int = 5

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "battery_docs"
```

환경변수는 `.env` 파일에서 읽는다.

## 도구 목록

| 도구 | 파일 | 상태 | 설명 |
|------|------|------|------|
| `search_web` | search_tools.py | ✅ | Tavily 웹 검색 |
| `fetch_google_news` | search_tools.py | ✅ | GoogleNews 뉴스 수집 |
| `read_pdf` | search_tools.py | ✅ | PDFPlumber PDF 파싱 |
| `analyze_swot` | analysis_tools.py | ✅ | SWOT 2×2 매트릭스 렌더링 |
| `search_battery_market_data` | market_tools.py | ❌ | 시장 규모/세그먼트 |
| `analyze_competitors` | market_tools.py | ❌ | 경쟁 포지셔닝 |
| `fetch_price_trends` | market_tools.py | ❌ | 원자재 가격 (yfinance) |
| `summarize_regulations` | market_tools.py | ❌ | 지역별 배터리 규제 |
