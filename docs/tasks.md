# 태스크 목록 (Tasks)

## 구현 완료 ✅

### 에이전트

- [x] **market_analysis_agent** — ReAct 패턴, Tavily + GoogleNews로 시장 동향 수집
- [x] **tech_analysis_agent** — RAG 기반 기업별 기술 문서 검색 및 분석
- [x] **swot_analysis_agent** — SWOT 서브그래프 오케스트레이터
- [x] **company_analysis_agent** — Supervisor 패턴, 3개 서브에이전트 조율
- [x] **report_generation_agent** — 구조화 출력 + 마크다운/PDF 렌더링

### 서브그래프

- [x] **SWOT 서브그래프** (`agents/swot/`) — gather → classify → format_matrix
- [x] **보고서 생성 서브그래프** — generate_sections → render_report

### 인프라

- [x] **BatteryRAG 싱글턴** — Qdrant 연동, 기업 메타데이터 필터링
- [x] **문서 인덱싱** (`rag/ingest.py`) — PDF 로딩, 청킹, 임베딩
- [x] **검색 도구** — search_web, fetch_google_news, read_pdf
- [x] **SWOT 매트릭스 렌더링** — analyze_swot (한국어 2바이트 패딩)
- [x] **설정 관리** — Pydantic Settings + .env

### State 정의

- [x] MarketAnalysisState
- [x] TechAnalysisState
- [x] SWOTState
- [x] CompanyAnalysisState
- [x] CompanyComparisonState
- [x] ReportState

---

## 미구현 ❌

### 우선순위 높음

- [ ] **BatteryMarketState 정의** (`state/graph_state.py`)
  - 현재 `Any` 플레이스홀더로 되어 있음
  - `query`, `retrieved_docs`, `company_report`, `comparison_report`, `final_report` 필드 추가 필요

- [ ] **retrieve_node 구현** (`agents/nodes.py`)
  - 현재 `raise NotImplementedError`
  - `BatteryRAG.retrieve()` 호출하여 공통 문서 검색
  - `BatteryMarketState.retrieved_docs` 에 결과 반환

- [ ] **company_comparison_agent 구현** (`agents/company_comparison_agent.py`)
  - 현재 `raise NotImplementedError`
  - LG vs CATL 비교 차원 정의 필요:
    - 기술 전략 (NCM vs LFP, 폼팩터)
    - 지역 전략 (북미/유럽/중국 시장)
    - 고객 전략 (OEM 파트너십)
    - 원가 전략 (생산 비용, 수직 계열화)
    - 신사업 (ESS, 배터리 재활용)
  - `CompanyComparisonState` 활용, `comparison_report` 출력

### 우선순위 중간

- [ ] **market_tools 구현** (`tools/market_tools.py`)
  - `search_battery_market_data` — 시장 데이터 API 연동
  - `fetch_price_trends` — yfinance로 원자재 가격 조회
  - `analyze_competitors` — 경쟁사 포지셔닝 분석
  - `summarize_regulations` — EU CBAM, IRA 등 규제 요약

- [ ] **main.py 진입점 완성**
  - BatteryMarketState 초기화
  - `run(query)` 함수 완성
  - 그래프 컴파일 및 스트리밍 출력

### 우선순위 낮음

- [ ] **기술 문서 수집 및 인덱싱**
  - `data/tech_docs/LG에너지솔루션/` 에 PDF 추가
  - `data/tech_docs/CATL/` 에 PDF 추가
  - `rag/ingest.py` 실행하여 Qdrant 인덱스 구축

- [ ] **엔드투엔드 테스트**
  - 전체 그래프 실행 테스트
  - 병렬 Send 동작 확인
  - 보고서 출력 품질 검증

---

## 작업 순서 (권장)

```
1. BatteryMarketState 정의
        ↓
2. retrieve_node 구현
        ↓
3. company_comparison_agent 구현
        ↓
4. main.py 완성
        ↓
5. 기술 문서 수집 & 인덱싱
        ↓
6. 엔드투엔드 실행 테스트
        ↓
7. market_tools 구현 (품질 개선)
```
