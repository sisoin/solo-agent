# 워크플로우 (Workflow)

## 전체 실행 흐름

```
사용자 입력 (query)
        ↓
  [retrieve_node]
  RAG 공통 문서 검색
        ↓
  [branch_companies]   ← Send API: 병렬 분기
    ↙         ↘
[company_analysis]  [company_analysis]
 LG에너지솔루션        CATL
    ↘         ↙
    자동 조인 (LangGraph)
        ↓
[company_comparison_agent]
 LG vs CATL 비교 분석
        ↓
[report_generation_agent]
 최종 보고서 생성
        ↓
 report_YYYYMMDD.md / .pdf
```

---

## 단계별 상세 흐름

### Step 1. retrieve_node

```
입력: query (str)
        ↓
BatteryRAG.retrieve(query)  → Qdrant 전체 검색
        ↓
출력: retrieved_docs (list[Document])  → BatteryMarketState
```

공통 문서(시장 보고서, 업계 개요 등)를 미리 검색하여 이후 에이전트에서 활용한다.

> ⚠️ 현재 미구현 (NotImplementedError)

---

### Step 2. company_analysis_agent (LG 및 CATL 병렬)

두 기업이 동일한 서브그래프를 독립적으로 실행한다.

#### 2-1. market_analysis_agent (ReAct)

```
입력: company (str)
        ↓
[LLM Reasoning]
    ↓  search_web("글로벌 배터리 시장 규모 {company}")
    ↓  fetch_google_news("{company} 배터리 최신 뉴스")
    ↓  search_web("배터리 원자재 가격 리튬 코발트")
    ↓  ... (LLM 판단에 따라 반복)
        ↓
출력: market_analysis (str)  → CompanyAnalysisState
```

수집 항목:
- 글로벌 배터리 시장 규모 & 성장률
- 기업별 시장점유율 & 포지셔닝
- 지역별 수요 (중국, 유럽, 북미)
- 원자재 가격 (리튬, 코발트, 니켈)
- 최신 뉴스 & 산업 이슈

#### 2-2. tech_analysis_agent (RAG)

```
입력: company (str), tech_queries (list[str])
        ↓
BatteryRAG.retrieve(query, company=company)  ← 기업 필터 적용
    ↓ × 6개 기본 쿼리
retrieved_docs (중복 제거)
        ↓
LLM 분석 (retrieved_docs 컨텍스트 기반)
        ↓
출력: tech_analysis (str)  → CompanyAnalysisState
```

기본 쿼리:
1. 배터리 셀 기술 & 에너지 밀도
2. 양극재 소재 (NCM, LFP, NCMA)
3. 음극재 소재 (실리콘, 흑연)
4. BMS (배터리 관리 시스템)
5. 제조 공정 & 원가
6. 차세대 기술 (전고체)

#### 2-3. swot_analysis_agent (서브그래프)

```
입력: company (str), market_trends (str)
        ↓
  [gather_info_node]
  search_web + fetch_google_news → raw_info 누적
        ↓
  [classify_swot_node]
  LLM.with_structured_output(SWOTItems)
  → strengths / weaknesses / opportunities / threats
        ↓
  [format_matrix_node]
  analyze_swot() → 2×2 ASCII 매트릭스
        ↓
출력: swot_matrix (str)  → CompanyAnalysisState
```

#### 2-4. Supervisor 종합

```
market_analysis + tech_analysis + swot_matrix
        ↓
Supervisor LLM 종합
        ↓
출력: company_report[company] (str)
```

---

### Step 3. company_comparison_agent

```
입력:
  company_report["LG에너지솔루션"] (str)
  company_report["CATL"] (str)
        ↓
비교 분석 LLM
  - 기술 전략 비교 (NCM vs LFP, 폼팩터)
  - 지역 전략 비교 (북미/유럽/중국)
  - 고객 전략 비교 (OEM 파트너십)
  - 원가 전략 비교
  - 신사업 비교 (ESS, 재활용)
        ↓
출력: comparison_report (str)  → BatteryMarketState
```

> ⚠️ 현재 미구현 (NotImplementedError)

---

### Step 4. report_generation_agent (서브그래프)

```
입력: company_report (dict), comparison_report (str)
        ↓
  [generate_sections_node]
  LLM.with_structured_output(ReportSections)
  → 구조화된 보고서 섹션 생성
        ↓
  [render_report_node]
  ReportSections → 마크다운 문자열
  + 파일 저장 (.md, .pdf)
        ↓
출력:
  final_report (str)
  report_md_path (str)
  report_pdf_path (str)
```

---

## 데이터 흐름 다이어그램

```
query
  │
  ▼
BatteryMarketState
  ├── retrieved_docs ────────────────── retrieve_node
  │
  ├── company_report["LG에너지솔루션"] ─ company_analysis (LG)
  │     ├── market_analysis               ← market_analysis_agent
  │     ├── tech_analysis                 ← tech_analysis_agent
  │     └── swot_matrix                   ← swot_analysis_agent
  │
  ├── company_report["CATL"] ──────────  company_analysis (CATL)
  │     (동일 구조)
  │
  ├── comparison_report ─────────────── company_comparison_agent
  │
  └── final_report ──────────────────── report_generation_agent
        ├── report_md_path
        └── report_pdf_path
```

---

## 보고서 구조

최종 보고서(`ReportSections` 스키마 기준):

```
SUMMARY
  핵심 인사이트 3~5줄

1. 시장 현황
  1.1 글로벌 배터리 시장 규모 & 개황
  1.2 시장 트렌드 & 구조 변화
  1.4 경쟁 구도

2. 기업 포트폴리오 & 기술 역량
  2.1 LG에너지솔루션: 포트폴리오 & 기술 역량
  2.2 CATL: 포트폴리오 & 기술 역량

3. 전략 비교 & SWOT
  3.1 전략 비교표 (5개 차원)
  3.2 SWOT 분석 & 시사점

4. 종합 분석
  4.1 전략적 포지셔닝 차이
  4.2 시장 전망
  4.3 투자 & 파트너십 의견

참고자료
```

---

## 실행 진입점

```python
# main.py
from battery_market_agent.agents.graph import build_graph

graph = build_graph()
result = graph.invoke({
    "query": "2025년 글로벌 배터리 시장 LG에너지솔루션 vs CATL 전략 분석"
})

print(result["final_report"])
# → report_YYYYMMDD_HHMMSS.md / .pdf 저장됨
```
