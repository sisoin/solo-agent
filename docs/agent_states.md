# Agent States

배터리 시장 전략 에이전트의 전체 그래프 흐름 및 각 에이전트 State 정의.

---

## 전체 흐름

```
START
  ↓
retrieve
  ↓
branch_companies (Send API — 회사별 병렬 분기)
  ├── [LG에너지솔루션]                      ├── [CATL]
  │   market_analysis_agent                 │   market_analysis_agent
  │   tech_analysis_agent     (병렬)        │   tech_analysis_agent     (병렬)
  │   swot_analysis_agent                   │   swot_analysis_agent
  │        ↓                                │        ↓
  │   company_analysis_agent (supervisor)   │   company_analysis_agent (supervisor)
  └────────────────────┬────────────────────┘
                       ↓  (양쪽 완료 후 자동 합류)
              company_comparison_agent
                       ↓
              report_generation_agent
                       ↓
                      END
```

---

## State 목록

| State | 위치 | 사용 에이전트 |
|-------|------|--------------|
| `MarketAnalysisState` | `agents/market/state.py` | market_analysis_agent |
| `TechAnalysisState` | `state/tech_analysis_state.py` | tech_analysis_agent |
| `SWOTState` | `agents/swot/state.py` | swot_analysis_agent (서브그래프) |
| `CompanyAnalysisState` | `state/company_analysis_state.py` | company_analysis_agent (supervisor) |
| `CompanyComparisonState` | `state/company_comparison_state.py` | company_comparison_agent |
| `ReportState` | `state/report_state.py` | report_generation_agent |

---

## MarketAnalysisState

**파일:** `agents/market/state.py`

```python
class MarketAnalysisState(TypedDict):
    company: str                      # 분석 대상 회사명
    market_size_raw: str              # 글로벌 시장 규모·성장률 웹 검색 결과
    regional_demand_raw: str          # 지역별 수요 동향 웹 검색 결과
    raw_material_prices_raw: str      # 원자재 가격 웹 검색 결과
    company_market_share_raw: str     # 기업 시장 점유율 웹 검색 결과
    battery_price_per_kwh_raw: str    # 배터리 팩 가격($/kWh) 추이 웹 검색 결과
    regulatory_policy_raw: str        # 규제·정책 웹 검색 결과
    news_items: list[str]             # 최신 뉴스 누적 (add reducer)
    market_analysis: str              # 최종 시장 분석 보고서
```

**흐름:** 6개 웹 검색 필드를 병렬 수집 → LLM으로 `market_analysis` 종합

---

## TechAnalysisState

**파일:** `state/tech_analysis_state.py`

```python
class TechAnalysisState(TypedDict):
    company: str                            # 분석 대상 회사명
    tech_queries: list[str]                 # RAG 검색 쿼리 목록
    retrieved_docs: list[Document]          # 쿼리별 RAG 검색 결과 누적 (add reducer)
    tech_analysis: str                      # 최종 기술 분석 결과
```

**흐름:** `tech_queries` 기반 RAG 검색 → `retrieved_docs` 누적 → LLM으로 `tech_analysis` 종합

---

## SWOTState

**파일:** `agents/swot/state.py`

```python
class SWOTState(TypedDict):
    subject: str                    # 분석 대상 (기업명)
    raw_info: list[str]             # gather_info 수집 원시 정보 누적 (add reducer)
    criteria: dict[str, str]        # 평가 기준 (strength / weakness / opportunity / threat)
    strengths: list[str]            # S — 내부 강점
    weaknesses: list[str]           # W — 내부 약점
    opportunities: list[str]        # O — 외부 기회
    threats: list[str]              # T — 외부 위협
    swot_matrix: str                # 최종 포맷된 2×2 행렬 문자열
```

**흐름:** `raw_info` 수집 → S/W/O/T 항목 분류 → `swot_matrix` 포맷팅

> **Note:** 독립 서브그래프로 동작. `company_analysis_agent`가 `run_swot_analysis` tool로 호출.

---

## CompanyAnalysisState

**파일:** `state/company_analysis_state.py`

```python
class CompanyAnalysisState(TypedDict):
    # 입력
    company: str                            # 분석 대상 회사명
    retrieved_docs: list[Document]          # 상위 그래프 RAG 결과

    # Supervisor 제어
    messages: list[AnyMessage]              # Supervisor tool-call 히스토리 (add_messages reducer)

    # 하위 에이전트 결과
    market_analysis: str                    # market_analysis_agent 출력
    tech_analysis: str                      # tech_analysis_agent 출력
    strengths: list[str]                    # swot_analysis_agent — S
    weaknesses: list[str]                   # swot_analysis_agent — W
    opportunities: list[str]               # swot_analysis_agent — O
    threats: list[str]                      # swot_analysis_agent — T
    swot_matrix: str                        # swot_analysis_agent — 2×2 행렬

    # 출력
    company_report: str                     # 세 에이전트 결과 종합 보고서
```

**흐름:** `langgraph_supervisor` 기반 — market → tech → swot 순서로 하위 에이전트 조율 후 `company_report` 생성

---

## CompanyComparisonState

**파일:** `state/company_comparison_state.py`

```python
class SWOTItems(TypedDict):
    strengths: list[str]        # 내부 강점 항목 목록
    weaknesses: list[str]       # 내부 약점 항목 목록
    opportunities: list[str]    # 외부 기회 항목 목록
    threats: list[str]          # 외부 위협 항목 목록
    swot_matrix: str            # 포맷된 2×2 행렬 문자열

class CompanyComparisonState(TypedDict):
    # 입력
    company_report: dict[str, str]              # {"LG에너지솔루션": "...", "CATL": "..."}
    market_analysis_by_company: dict[str, str]  # 기업별 시장 분석 텍스트
    tech_analysis_by_company: dict[str, str]    # 기업별 기술 역량 분석 텍스트
    swot_by_company: dict[str, SWOTItems]       # 기업별 SWOT 세부 항목

    # 비교 기준 (TODO: 미정)

    # 출력
    comparison_report: str                      # 종합 비교 분석 텍스트
```

**흐름:** LG·CATL `company_analysis_agent` 병렬 완료 후 합류 → 비교 분석 수행 → `comparison_report` 생성

> **Note:** 비교 평가 기준 미확정. 기준 확정 시 `# TODO` 섹션에 `comparison_dimensions`, `scoring_rubric` 등 필드 추가 예정.

---

## ReportState

**파일:** `state/report_state.py`

```python
class ReportState(TypedDict):
    # 입력
    company_report: dict[str, str]    # {"LG에너지솔루션": "...", "CATL": "..."}
    comparison_report: str            # company_comparison_agent 비교 보고서

    # 중간 산출물
    sections: ReportSections | None   # LLM structured output 결과

    # 출력
    final_report: str                 # 마크다운 최종 보고서
    report_md_path: str               # 저장된 마크다운 보고서 파일 경로
    report_pdf_path: str              # 저장된 PDF 보고서 파일 경로
```

### ReportSections (structured output 스키마)

`LLM.with_structured_output(ReportSections)`으로 한 번에 생성되는 보고서 섹션 구조.

| 필드 | 설명 |
|------|------|
| `summary` | 핵심 인사이트 3~5줄 요약 |
| `market_overview` | 1.1 글로벌 배터리 시장 현황 |
| `market_trends` | 1.2 시장 구조 변화 및 트렌드 |
| `competitive_landscape` | 1.4 경쟁 구도 개요 |
| `lg_portfolio` / `catl_portfolio` | 2.x 기업별 사업 포트폴리오 |
| `lg_tech` / `catl_tech` | 2.x 기업별 기술 경쟁력 |
| `strategy_tech/region/customer/cost/new_biz` | 3.x 전략 비교 (`StrategyRow`) |
| `swot_lg` / `swot_catl` | 3.2 SWOT 항목 (`SWOTDetail`) |
| `swot_sw_implications` / `swot_ot_implications` | 3.2.3 SWOT 비교 시사점 |
| `positioning_diff` | 4.1 전략적 포지셔닝 차이 |
| `market_outlook` | 4.2 시장 향후 전망 |
| `investment_opinion` | 4.3 투자·협력 관점 의견 |
| `references` | 참고문헌 목록 |
