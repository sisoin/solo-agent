"""
보고서 생성 에이전트

역할:
    기업 분석 에이전트(company_analysis_agent)와
    회사 비교 에이전트(company_comparison_agent)의 결과를 종합하여
    정해진 양식의 마크다운 보고서를 생성한다.

처리 흐름:
    1. generate_sections_node : LLM.with_structured_output으로 섹션 데이터 생성
    2. render_report_node     : 섹션 데이터를 보고서 마크다운 양식으로 렌더링

입력 (ReportState):
    company_report    : 기업 분석 결과 {"LG에너지솔루션": "...", "CATL": "..."}
    comparison_report : 비교 분석 결과 (SWOT 포함)

출력 (ReportState):
    sections     : 구조화된 섹션 데이터 (중간 산출물)
    final_report : 최종 마크다운 보고서
"""
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

from battery_market_agent.config import Settings
from battery_market_agent.state.report_state import ReportState, ReportSections

_settings = Settings()
_llm = ChatAnthropic(
    model=_settings.model_name,
    api_key=_settings.anthropic_api_key,
)
_structured_llm = _llm.with_structured_output(ReportSections)


# ---------------------------------------------------------------------------
# 노드 1 : 섹션 데이터 생성
# ---------------------------------------------------------------------------

def generate_sections_node(state: ReportState) -> dict:
    """
    company_report와 comparison_report를 컨텍스트로
    LLM.with_structured_output을 호출하여 ReportSections를 생성한다.
    """
    company_report: dict    = state.get("company_report", {})
    comparison_report: str  = state.get("comparison_report", "")

    context = "\n\n".join([
        "=== 기업별 분석 보고서 ===",
        *[f"## {company}\n{report}" for company, report in company_report.items()],
        "=== 비교 분석 보고서 (SWOT 포함) ===",
        comparison_report,
    ])

    prompt = f"""다음은 LG에너지솔루션과 CATL에 대해 수집·분석된 정보입니다.
이 정보를 바탕으로 배터리 기업 전략 분석 보고서의 각 섹션을 작성하세요.
분석은 구체적이고 데이터 기반으로 작성하며, 한국어로 작성하세요.

{context}"""

    sections: ReportSections = _structured_llm.invoke(prompt)
    return {"sections": sections}


# ---------------------------------------------------------------------------
# 노드 2 : 보고서 마크다운 렌더링
# ---------------------------------------------------------------------------

def render_report_node(state: ReportState) -> dict:
    """
    ReportSections 구조체를 보고서 양식(마크다운)으로 렌더링하여
    final_report에 저장한다.
    """
    s = state["sections"]

    def _strategy_table() -> str:
        rows = [
            ("기술 방향성", s.strategy_tech),
            ("지역 전략",   s.strategy_region),
            ("고객 전략",   s.strategy_customer),
            ("원가 전략",   s.strategy_cost),
            ("신사업 방향", s.strategy_new_biz),
        ]
        lines = [
            "| 전략 항목 | LG에너지솔루션 | CATL |",
            "| --- | --- | --- |",
        ]
        for label, row in rows:
            lines.append(f"| {label} | {row.lg} | {row.catl} |")
        return "\n".join(lines)

    def _swot_table(swot) -> str:
        return "\n".join([
            "| 구분 | 내용 |",
            "| --- | --- |",
            f"| **S** (강점 / 내부) | {swot.strength} |",
            f"| **W** (약점 / 내부) | {swot.weakness} |",
            f"| **O** (기회 / 외부) | {swot.opportunity} |",
            f"| **T** (위협 / 외부) | {swot.threat} |",
        ])

    def _references() -> str:
        return "\n".join(f"- {ref}" for ref in s.references)

    report = f"""# 배터리 기업 전략 분석 보고서

## CATL vs LG에너지솔루션

---

## SUMMARY

{s.summary}

---

## 1. 시장 배경 : 글로벌 배터리 시장 환경 변화

### 1.1 글로벌 배터리 시장 현황 및 규모

{s.market_overview}

### 1.2 시장 구조 변화 및 핵심 트렌드

{s.market_trends}

### 1.4 경쟁 구도 개요

{s.competitive_landscape}

---

## 2. 기업별 포트폴리오 다각화 전략 및 핵심 경쟁력

### 2.1 LG에너지솔루션

### 2.1.1 사업 포트폴리오 구성

{s.lg_portfolio}

### 2.1.2 기술 경쟁력

{s.lg_tech}

---

### 2.2 CATL

### 2.2.1 사업 포트폴리오 구성

{s.catl_portfolio}

### 2.2.2 기술 경쟁력

{s.catl_tech}

---

## 3. 핵심 전략 비교 및 SWOT 분석

### 3.1 핵심 전략 비교

{_strategy_table()}

### 3.2 SWOT 분석

### 3.2.1 LG에너지솔루션 SWOT

{_swot_table(s.swot_lg)}

### 3.2.2 CATL SWOT

{_swot_table(s.swot_catl)}

### 3.2.3 SWOT 비교 시사점

- **내부 역량(S/W) 관점**: {s.swot_sw_implications}
- **외부 환경(O/T) 관점**: {s.swot_ot_implications}

---

## 4. 종합 시사점

### 4.1 두 기업의 전략적 포지셔닝 차이

{s.positioning_diff}

### 4.2 배터리 시장 향후 전망과 시사점

{s.market_outlook}

### 4.3 투자·협력 관점 종합 의견

{s.investment_opinion}

---

## REFERENCE

{_references()}
"""
    return {"final_report": report.strip()}


# ---------------------------------------------------------------------------
# 서브그래프
# ---------------------------------------------------------------------------

def build_report_graph():
    graph = StateGraph(ReportState)

    graph.add_node("generate_sections", generate_sections_node)
    graph.add_node("render_report",     render_report_node)

    graph.set_entry_point("generate_sections")
    graph.add_edge("generate_sections", "render_report")
    graph.add_edge("render_report", END)

    return graph.compile()


_report_graph = build_report_graph()


# ---------------------------------------------------------------------------
# 메인 그래프 노드 래퍼
# ---------------------------------------------------------------------------

def report_generation_agent(state) -> dict:
    """
    보고서 생성 에이전트 노드.

    company_report와 comparison_report를 받아
    _report_graph를 실행하고 final_report를 반환한다.
    """
    result = _report_graph.invoke({
        "company_report":    state.get("company_report", {}),
        "comparison_report": state.get("comparison_report", ""),
        "sections":          None,
        "final_report":      "",
    })

    return {"final_report": result["final_report"]}
