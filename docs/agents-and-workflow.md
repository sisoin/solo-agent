# Battery Market Agent — 에이전트 & 워크플로우

## 목차

1. [전체 워크플로우](#1-전체-워크플로우)
2. [최상위 그래프](#2-최상위-그래프)
3. [에이전트 상세](#3-에이전트-상세)
   - [3-1. market_analysis_agent](#3-1-market_analysis_agent)
   - [3-2. tech_analysis_agent](#3-2-tech_analysis_agent)
   - [3-3. swot_analysis_agent](#3-3-swot_analysis_agent)
   - [3-4. company_analysis_agent (Supervisor)](#3-4-company_analysis_agent-supervisor)
   - [3-5. company_comparison_agent](#3-5-company_comparison_agent)
   - [3-6. report_generation_agent](#3-6-report_generation_agent)
4. [State 정의](#4-state-정의)
   - [MarketAnalysisState](#marketanalysisstate)
   - [TechAnalysisState](#techanalysisstate)
   - [SWOTState](#swotstate)
   - [CompanyAnalysisState](#companyanalysisstate)
   - [BatteryMarketState](#batterymarketstate)
5. [도구 목록](#5-도구-목록)
6. [구현 현황](#6-구현-현황)

---

## 1. 전체 워크플로우

```
START
  │
  ▼
retrieve ──────────────────────────────────── RAG로 공통 기술 문서 검색
  │
  ▼ branch_companies (Send API — 병렬 분기)
  ├──────────────────────┬─────────────────────────┐
  │  [LG에너지솔루션]    │           [CATL]         │
  │                      │                          │
  ▼                      ▼                          │
company_analysis_agent (Supervisor)                 │
  ├─ market_analysis_agent  ← 웹 서치 기반 시장 분석 │
  ├─ tech_analysis_agent    ← RAG 기반 기술 역량 분석│
  └─ swot_analysis_agent    ← SWOT 서브그래프 실행  │
  │                                                 │
  └──────────────────────────────────────────────── ┘
                           │ (양쪽 완료 후 자동 합류)
                           ▼
               company_comparison_agent ──── 두 기업 비교 분석
                           │
                           ▼
               report_generation_agent ───── 최종 전략 보고서 생성
                           │
                           ▼
                          END
```

### SWOT 서브그래프 (내부)

```
gather_info_node ──► classify_swot_node ──► format_matrix_node ──► END
  (웹 검색·뉴스)     (S/W/O/T 분류)          (2×2 행렬 렌더링)
```

---

## 2. 최상위 그래프

**파일:** `battery_market_agent/agents/graph.py`

| 노드 | 함수 | 역할 |
|------|------|------|
| `retrieve` | `retrieve_node` | RAG로 공통 기술 문서 검색 |
| `company_analysis` | `company_analysis_agent` | 단일 기업 Supervisor (LG·CATL 각각 병렬 실행) |
| `company_comparison` | `company_comparison_agent` | 두 기업 결과 합류 후 비교 분석 |
| `report_generation` | `report_generation_agent` | 최종 전략 보고서 생성 |

**분기 로직:** `branch_companies(state)` — LangGraph `Send` API로 `company_analysis` 노드를 두 회사에 대해 동시 실행

---

## 3. 에이전트 상세

### 3-1. market_analysis_agent

**파일:** `battery_market_agent/agents/market_analysis_agent.py`
**구현 상태:** ✅ 구현 완료

**역할:** Tavily 웹 서치와 Google News로 배터리 시장 동향을 수집·분석한다.

**사용 도구:**
- `search_web` (Tavily) — 시장 규모·성장률, 원자재 가격, 점유율, 배터리 단가, 규제 검색
- `fetch_google_news` — 최신 뉴스·이슈 수집
- `fetch_price_trends` — 원자재 가격 추이 조회

**실행 방식:** `create_react_agent` (ReAct 루프) — LLM이 도구를 반복 호출하며 정보 수집

**입력 → 출력:**
```
state["company"]  →  state["market_trends"][company]
```

**시스템 프롬프트 조사 항목:**
1. 글로벌 배터리 시장 규모 및 성장률
2. 해당 기업의 시장 점유율 및 포지셔닝
3. 지역별 수요 동향 (중국·유럽·북미)
4. 원자재 가격 동향 (리튬·코발트·니켈)
5. 최신 뉴스 및 산업 이슈

---

### 3-2. tech_analysis_agent

**파일:** `battery_market_agent/agents/tech_analysis_agent.py`
**구현 상태:** ✅ 구현 완료

**역할:** `BatteryRAG`로 회사별 기술 PDF를 검색하고 LLM으로 기술 역량을 분석한다.

**RAG 문서 경로:**
```
data/tech_docs/
  ├── LG에너지솔루션/   ← 기술 PDF (특허, 기술보고서 등)
  └── CATL/             ← 기술 PDF
```

**기본 검색 쿼리 (tech_queries 미입력 시):**
배터리 셀 기술/에너지 밀도, 양극재(NCM·LFP·NCMA), 음극재, BMS, 생산 공정, 차세대(전고체) 기술

**실행 흐름:**
1. `tech_queries` 각각으로 `BatteryRAG.retrieve(query, company=company)` 호출
2. 중복 청크 제거 (source + page 기준)
3. 검색 문서를 컨텍스트로 LLM 기술 분석 보고서 생성

**입력 → 출력:**
```
state["company"], state["tech_queries"]  →  state["retrieved_docs"], state["tech_analysis"]
```

---

### 3-3. swot_analysis_agent

**파일:** `battery_market_agent/agents/swot_analysis_agent.py`
**구현 상태:** ✅ 구현 완료

**역할:** `market_analysis_agent` 결과를 받아 SWOT 서브그래프를 실행하고 2×2 행렬을 반환한다.

**입력 → 출력:**
```
state["company"], state["market_trends"][company]  →  state["swot_table"][company]
```

**내부 서브그래프 흐름:**

| 노드 | 함수 | 역할 |
|------|------|------|
| `gather_info` | `gather_info_node` | 구글 뉴스 + 웹 검색으로 원시 정보 수집 |
| `classify_swot` | `classify_swot_node` | LLM 구조화 출력으로 S/W/O/T 항목 분류 |
| `format_matrix` | `format_matrix_node` | `analyze_swot` 도구로 2×2 행렬 렌더링 |

---

### 3-4. company_analysis_agent (Supervisor)

**파일:** `battery_market_agent/agents/company_analysis_agent.py`
**구현 상태:** ✅ 구현 완료

**역할:** `create_supervisor`로 세 하위 에이전트를 순차 조율하고 종합 기업 보고서를 생성한다.
LG에너지솔루션·CATL 각각에 대해 독립적으로(병렬) 실행된다.

**실행 흐름:**
```
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
swot_analysis_agent    →  결과 반환 (run_swot_analysis 도구 → SWOT 서브그래프)
  ↓ transfer_back_to_supervisor
supervisor (LLM) — 세 결과 종합 후 종료
```

**하위 에이전트 구성:**

| 에이전트 | 구현 방식 | 사용 도구 |
|----------|-----------|-----------|
| `market_analysis_agent` | `create_react_agent` (market_analysis_agent.py 재사용) | search_web, fetch_google_news |
| `tech_analysis_agent` | `create_react_agent` | read_pdf, search_web |
| `swot_analysis_agent` | `create_react_agent` | run_swot_analysis (SWOT 서브그래프 래핑), search_web, fetch_google_news |

**Supervisor 설정:** `add_handoff_back_messages=True`, `output_mode="last_message"`

**입력 → 출력:**
```
state["company"]  →  state["company_report"][company]
```

---

### 3-5. company_comparison_agent

**파일:** `battery_market_agent/agents/company_comparison_agent.py`
**구현 상태:** ❌ 미구현 (NotImplementedError)

**역할:** LG에너지솔루션·CATL 두 기업의 분석 결과를 비교한다.
`company_analysis_agent` 두 인스턴스가 모두 완료된 후 실행된다.

**입력 → 출력:**
```
state["company_report"]["LG에너지솔루션"]
state["company_report"]["CATL"]
  →  state["comparison_report"]
```

---

### 3-6. report_generation_agent

**파일:** `battery_market_agent/agents/report_generation_agent.py`
**구현 상태:** ✅ 구현 완료

**역할:** `company_report`와 `comparison_report`를 입력받아 정해진 마크다운 양식의 최종 전략 보고서를 생성한다.

**내부 서브그래프 흐름:**
```
generate_sections_node  →  render_report_node  →  END
  (LLM structured output)    (마크다운 렌더링)
```

| 노드 | 함수 | 역할 |
|------|------|------|
| `generate_sections` | `generate_sections_node` | `LLM.with_structured_output(ReportSections)` 으로 섹션 데이터 일괄 생성 |
| `render_report` | `render_report_node` | `ReportSections` 구조체를 보고서 마크다운 양식으로 렌더링 |

**보고서 목차:**
- SUMMARY
- 1. 시장 배경 (1.1 시장 현황·규모, 1.2 핵심 트렌드, 1.4 경쟁 구도)
- 2. 기업별 포트폴리오 및 기술 경쟁력 (LG에너지솔루션 / CATL)
- 3. 핵심 전략 비교 + SWOT 분석 (2×2 테이블, 시사점)
- 4. 종합 시사점 (포지셔닝 차이, 시장 전망, 투자·협력 의견)
- REFERENCE

**입력 → 출력:**
```
state["company_report"], state["comparison_report"]  →  state["final_report"]
```

---

## 4. State 정의

### MarketAnalysisState

**파일:** `battery_market_agent/agents/market/state.py`

```python
class MarketAnalysisState(TypedDict):
```

| 필드 | 타입 | 구분 | 설명 |
|------|------|------|------|
| `company` | `str` | 입력 | 분석 대상 회사명 |
| `market_size_raw` | `str` | 웹 검색 결과 | 글로벌 시장 규모·성장률 원시 텍스트 |
| `regional_demand_raw` | `str` | 웹 검색 결과 | 중국·유럽·북미 지역별 수요 원시 텍스트 |
| `raw_material_prices_raw` | `str` | 웹 검색 결과 | 리튬·코발트·니켈 가격 원시 텍스트 |
| `company_market_share_raw` | `str` | 웹 검색 결과 | 대상 기업 시장 점유율 원시 텍스트 |
| `battery_price_per_kwh_raw` | `str` | 웹 검색 결과 | 배터리 팩 단가($/kWh) 추이 원시 텍스트 |
| `regulatory_policy_raw` | `str` | 웹 검색 결과 | EU 규제·IRA 정책 원시 텍스트 |
| `news_items` | `Annotated[list[str], add]` | 웹 검색 결과 | 최신 뉴스·이슈 목록 (검색 호출마다 누적) |
| `market_analysis` | `str` | 최종 결과 | LLM 종합 시장 분석 보고서 |

---

### TechAnalysisState

**파일:** `battery_market_agent/state/tech_analysis_state.py`

```python
class TechAnalysisState(TypedDict):
```

| 필드 | 타입 | 구분 | 설명 |
|------|------|------|------|
| `company` | `str` | 입력 | 분석 대상 회사명 |
| `tech_queries` | `list[str]` | 입력 | RAG 검색에 사용할 기술 쿼리 목록 |
| `retrieved_docs` | `Annotated[list[Document], add]` | 중간 결과 | 쿼리별 RAG 검색 결과 (누적) |
| `tech_analysis` | `str` | 최종 결과 | 최종 기술 역량 분석 결과 |

---

### SWOTState

**파일:** `battery_market_agent/agents/swot/state.py`
*(SWOT 서브그래프 전용)*

```python
class SWOTState(TypedDict):
```

| 필드 | 타입 | 구분 | 설명 |
|------|------|------|------|
| `subject` | `str` | 입력 | 분석 대상 (기업명 등) |
| `raw_info` | `Annotated[list[str], add]` | 중간 결과 | `gather_info_node`가 누적한 원시 정보 |
| `criteria` | `dict[str, str]` | 입력 (선택) | S/W/O/T별 평가 기준 |
| `strengths` | `list[str]` | 중간 결과 | 내부 강점 항목 목록 |
| `weaknesses` | `list[str]` | 중간 결과 | 내부 약점 항목 목록 |
| `opportunities` | `list[str]` | 중간 결과 | 외부 기회 항목 목록 |
| `threats` | `list[str]` | 중간 결과 | 외부 위협 항목 목록 |
| `swot_matrix` | `str` | 최종 결과 | 2×2 SWOT 행렬 문자열 |

---

### CompanyAnalysisState

**파일:** `battery_market_agent/state/company_analysis_state.py`

```python
class CompanyAnalysisState(TypedDict):
```

| 필드 | 타입 | 구분 | 설명 |
|------|------|------|------|
| `company` | `str` | 입력 | 분석 대상 회사명 |
| `retrieved_docs` | `list[Document]` | 입력 | 상위 그래프에서 전달된 RAG 검색 결과 |
| `messages` | `Annotated[list[AnyMessage], add_messages]` | Supervisor 내부 | Supervisor LLM 대화 히스토리 |
| `market_analysis` | `str` | 하위 에이전트 결과 | market_analysis_agent 최종 보고서 |
| `tech_analysis` | `str` | 하위 에이전트 결과 | tech_analysis_agent 최종 기술 분석 |
| `strengths` | `list[str]` | 하위 에이전트 결과 | SWOT 강점 목록 |
| `weaknesses` | `list[str]` | 하위 에이전트 결과 | SWOT 약점 목록 |
| `opportunities` | `list[str]` | 하위 에이전트 결과 | SWOT 기회 목록 |
| `threats` | `list[str]` | 하위 에이전트 결과 | SWOT 위협 목록 |
| `swot_matrix` | `str` | 하위 에이전트 결과 | 2×2 SWOT 행렬 문자열 |
| `company_report` | `str` | 최종 출력 | Supervisor가 종합한 단일 기업 분석 보고서 |

---

### ReportState

**파일:** `battery_market_agent/state/report_state.py`
*(report_generation_agent 서브그래프 전용)*

```python
class ReportState(TypedDict):
```

| 필드 | 타입 | 구분 | 설명 |
|------|------|------|------|
| `company_report` | `dict[str, str]` | 입력 | 기업 분석 Supervisor 결과 (`{"LG에너지솔루션": ..., "CATL": ...}`) |
| `comparison_report` | `str` | 입력 | 회사 비교 에이전트 결과 |
| `sections` | `ReportSections \| None` | 중간 결과 | LLM structured output 섹션 데이터 |
| `final_report` | `str` | 최종 출력 | 마크다운 렌더링된 최종 보고서 |

**`ReportSections` (Pydantic BaseModel)** — `generate_sections_node`에서 LLM이 한 번에 생성하는 구조:

| 필드 그룹 | 필드 | 설명 |
|-----------|------|------|
| SUMMARY | `summary` | 핵심 인사이트 3~5줄 |
| 1. 시장 배경 | `market_overview`, `market_trends`, `competitive_landscape` | 시장 현황·트렌드·경쟁 구도 |
| 2. 기업 포트폴리오 | `lg_portfolio`, `lg_tech`, `catl_portfolio`, `catl_tech` | 사업 포트폴리오 + 기술 경쟁력 |
| 3. 전략 비교 | `strategy_tech/region/customer/cost/new_biz` (`StrategyRow`) | LG vs CATL 전략 비교표 |
| 3. SWOT | `swot_lg`, `swot_catl` (`SWOTDetail`), `swot_sw_implications`, `swot_ot_implications` | SWOT 테이블 + 시사점 |
| 4. 종합 | `positioning_diff`, `market_outlook`, `investment_opinion` | 포지셔닝·전망·투자 의견 |
| 참고 | `references` | 출처 목록 |

---

### BatteryMarketState

**파일:** `battery_market_agent/state/graph_state.py`
**구현 상태:** ❌ 미정의 (현재 `Any` 플레이스홀더)

최상위 그래프 전체를 관통하는 공유 상태. 정의 예정 필드:

| 필드 | 타입 | 설명 |
|------|------|------|
| `query` | `str` | 사용자 입력 쿼리 |
| `retrieved_docs` | `list[Document]` | `retrieve_node` RAG 결과 |
| `company_report` | `dict[str, str]` | 기업별 분석 보고서 (`{"LG에너지솔루션": ..., "CATL": ...}`) |
| `comparison_report` | `str` | 두 기업 비교 분석 결과 |
| `final_report` | `str` | 최종 전략 보고서 |

---

## 5. 도구 목록

### 검색 도구 (`tools/search_tools.py`)

| 도구 | 구현 | 설명 |
|------|------|------|
| `search_web` | ✅ | Tavily API 웹 검색 |
| `fetch_google_news` | ✅ | GoogleNews 뉴스 검색 |
| `read_pdf` | ✅ | PDFPlumberLoader PDF 읽기 |

### 시장 도구 (`tools/market_tools.py`)

| 도구 | 구현 | 설명 |
|------|------|------|
| `search_battery_market_data` | ❌ | 배터리 시장 규모·세그먼트 데이터 검색 |
| `analyze_competitors` | ❌ | 경쟁사 포지셔닝 분석 |
| `fetch_price_trends` | ❌ | 원자재 가격 추이 조회 (yfinance 예정) |
| `summarize_regulations` | ❌ | 지역별 배터리 규제·정책 요약 |

### 분석 도구 (`tools/analysis_tools.py`)

| 도구 | 구현 | 설명 |
|------|------|------|
| `analyze_swot` | ✅ | SWOT 항목 → 2×2 행렬 텍스트 렌더링 |

---

## 6. 구현 현황

| 컴포넌트 | 구현 상태 | 비고 |
|----------|----------|------|
| `market_analysis_agent` | ✅ 완료 | ReAct + Tavily/GoogleNews, name 파라미터 추가 |
| `tech_analysis_agent` | ✅ 완료 | BatteryRAG + LLM 직접 호출 |
| `swot_analysis_agent` | ✅ 완료 | SWOT 서브그래프 래퍼 |
| `company_analysis_agent` | ✅ 완료 | `create_supervisor` + 3 하위 에이전트 |
| `report_generation_agent` | ✅ 완료 | 2-노드 서브그래프 (generate → render) |
| SWOT 서브그래프 (3노드) | ✅ 완료 | gather → classify → format |
| `MarketAnalysisState` | ✅ 완료 | 웹 검색 7개 필드 + 최종 결과 |
| `TechAnalysisState` | ✅ 완료 | RAG 쿼리 + 누적 docs + 결과 |
| `SWOTState` | ✅ 완료 | subject + raw_info + S/W/O/T + matrix |
| `CompanyAnalysisState` | ✅ 완료 | Supervisor + 하위 에이전트 결과 통합 |
| `ReportState` / `ReportSections` | ✅ 완료 | 보고서 섹션 구조체 + State |
| `company_comparison_agent` | ❌ 미구현 | 비교 항목 정의 필요 |
| `retrieve_node` | ❌ 미구현 | BatteryRAG.retrieve() 연동 필요 |
| `BatteryMarketState` | ❌ 미정의 | `Any` 플레이스홀더 |
| `fetch_price_trends` | ❌ 미구현 | yfinance 연동 예정 |
| `search_battery_market_data` | ❌ 미구현 | — |
| `analyze_competitors` | ❌ 미구현 | — |
| `summarize_regulations` | ❌ 미구현 | RAG 연동 예정 |
