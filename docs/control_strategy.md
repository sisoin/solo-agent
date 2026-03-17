# 제어 전략 (Control Strategy)

## 에이전트 제어 패턴 개요

이 시스템은 세 가지 제어 패턴을 계층적으로 조합하여 사용한다.

```
최상위 그래프  →  순차 실행 (DAG)
    ↓
병렬 분기     →  LangGraph Send API (LG / CATL 동시 실행)
    ↓
기업 분석     →  Supervisor (LLM이 서브에이전트 호출 순서 결정)
    ↓
SWOT / 보고서  →  순차 서브그래프 (고정 노드 순서)
    ↓
시장 분석     →  ReAct (도구 호출 루프)
```

---

## 1. ReAct 루프 — market_analysis_agent

**사용 위치:** market_analysis_agent

**패턴:** `create_react_agent(llm, tools)`

에이전트가 도구 호출(Thought → Action → Observation)을 반복하며 필요한 정보를 스스로 수집한다.

```
[LLM Reasoning]
    ↓ (tool_call)
[search_web / fetch_google_news]
    ↓ (tool_result)
[LLM Reasoning]
    ↓ ... (반복)
[최종 분석 텍스트 출력]
```

**제어 포인트:**
- 시스템 프롬프트로 수집 항목 지정 (시장 규모, 지역 수요, 원자재 가격 등)
- 도구 결과가 state의 raw 필드에 누적됨 (`Annotated[list, add]` reducer)
- LLM이 충분한 정보 수집을 판단하면 루프 종료

---

## 2. 순차 서브그래프 — SWOT, 보고서 생성

**사용 위치:** swot_analysis_agent, report_generation_agent

**패턴:** 고정 순서의 노드 체인

노드 간 데이터 흐름이 단방향으로 고정되어 있어 실행 순서가 보장된다.

### SWOT 서브그래프
```
gather_info_node  →  classify_swot_node  →  format_matrix_node
    (웹 검색)          (LLM 구조화 출력)       (2×2 매트릭스 렌더링)
```

### 보고서 생성 서브그래프
```
generate_sections_node  →  render_report_node
  (LLM → ReportSections)    (마크다운/PDF 저장)
```

**제어 포인트:**
- `with_structured_output(ReportSections)` — LLM 출력을 Pydantic 스키마로 강제 파싱
- 각 노드는 state를 수정하고 다음 노드로 전달

---

## 3. Supervisor — company_analysis_agent

**사용 위치:** company_analysis_agent

**패턴:** `create_supervisor(llm, agents=[market, tech, swot])`

Supervisor LLM이 세 서브에이전트의 호출 순서와 handoff를 동적으로 결정한다.

```
[Supervisor LLM]
    ↓ handoff
[market_analysis_agent]  →  market_analysis 결과
    ↓ handoff
[tech_analysis_agent]    →  tech_analysis 결과
    ↓ handoff
[swot_analysis_agent]    →  swot_matrix 결과
    ↓ (Supervisor가 종합)
[company_report 생성]
```

**설정:**
```python
create_supervisor(
    llm,
    agents=[market_agent, tech_agent, swot_agent],
    add_handoff_back_messages=True,
    output_mode="last_message",
)
```

**제어 포인트:**
- Supervisor가 각 에이전트 완료 후 다음 호출 대상을 결정
- `add_handoff_back_messages=True` — 서브에이전트 결과를 Supervisor 컨텍스트에 포함
- 최종 `company_report`는 Supervisor가 전체 결과를 종합하여 생성

---

## 4. 병렬 분기 — Send API

**사용 위치:** 최상위 graph.py (`branch_companies` 엣지)

**패턴:** LangGraph `Send` API

두 기업(LG에너지솔루션, CATL)에 대해 `company_analysis_agent`를 동시에 실행한다.

```python
def branch_companies(state: BatteryMarketState):
    return [
        Send("company_analysis", {"company": "LG에너지솔루션"}),
        Send("company_analysis", {"company": "CATL"}),
    ]
```

```
retrieve_node
     ↓
  ┌──┴──┐
  ↓     ↓   (병렬 실행)
[LG]  [CATL]
  ↓     ↓
  └──┬──┘   (자동 조인)
     ↓
company_comparison_agent
```

**제어 포인트:**
- 두 인스턴스는 완전히 독립적으로 실행
- LangGraph가 자동으로 조인 (명시적 동기화 불필요)
- 각 인스턴스의 결과는 `company_report` dict에 기업명 키로 병합됨

---

## 5. LLM 구조화 출력 (Structured Output)

**사용 위치:** classify_swot_node, generate_sections_node

**패턴:** `llm.with_structured_output(PydanticModel)`

LLM 자유 텍스트 출력을 Pydantic 스키마로 파싱하여 일관된 데이터 구조를 보장한다.

```python
# SWOT 분류
chain = llm.with_structured_output(SWOTItems)
result: SWOTItems = chain.invoke(prompt)

# 보고서 섹션 생성
chain = llm.with_structured_output(ReportSections)
result: ReportSections = chain.invoke(prompt)
```

**효과:**
- 출력 형식 오류로 인한 파이프라인 중단 방지
- 후속 노드가 타입 안전하게 데이터 접근 가능

---

## 6. RAG 필터링 전략

**사용 위치:** tech_analysis_agent, retrieve_node

Qdrant 벡터 검색 시 `company` 메타데이터 필터를 적용하여 기업별 문서만 검색한다.

```python
rag.retrieve(query="solid-state battery", company="LG에너지솔루션")
# → LG에너지솔루션 문서만 검색 (CATL 문서 제외)
```

각 기업 분석이 자신의 문서 컨텍스트만 참조하므로 교차 오염이 방지된다.

---

## 제어 전략 요약

| 레이어 | 패턴 | 결정 주체 | 유연성 |
|--------|------|-----------|--------|
| 시장 정보 수집 | ReAct 루프 | 에이전트 LLM | 높음 |
| SWOT 분석 | 순차 서브그래프 | 고정 노드 순서 | 낮음 |
| 보고서 생성 | 순차 서브그래프 | 고정 노드 순서 | 낮음 |
| 단일 기업 분석 | Supervisor | Supervisor LLM | 중간 |
| 기업 간 병렬 실행 | Send API | LangGraph 런타임 | — |
| 출력 형식 보장 | Structured Output | Pydantic 스키마 | 낮음 |
