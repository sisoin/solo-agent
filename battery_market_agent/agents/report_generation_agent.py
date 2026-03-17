"""
보고서 생성 에이전트

역할:
    기업 분석 에이전트(company_analysis_agent)와
    회사 비교 에이전트(company_comparison_agent)의 결과를 종합하여
    정해진 양식의 마크다운 보고서를 생성한다.

처리 흐름:
    1. generate_sections_node : LLM.with_structured_output으로 섹션 데이터 생성
    2. render_report_node     : 섹션 데이터를 보고서 마크다운 양식으로 렌더링 + 파일 저장

입력 (ReportState):
    company_report    : 기업 분석 결과 {"LG에너지솔루션": "...", "CATL": "..."}
    comparison_report : 비교 분석 결과 (SWOT 포함)

출력 (ReportState):
    sections        : 구조화된 섹션 데이터 (중간 산출물)
    final_report    : 최종 마크다운 보고서
    report_md_path  : 저장된 마크다운 파일 경로 (docs/report_<timestamp>.md)
    report_pdf_path : 저장된 PDF 파일 경로 (docs/report_<timestamp>.pdf)
"""
import os
import re
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from battery_market_agent.config import Settings
from battery_market_agent.state.report_state import ReportState, ReportSections

# ---------------------------------------------------------------------------
# 한글 폰트 등록 (macOS 기본 폰트 사용)
# ---------------------------------------------------------------------------
_FONT_PATHS = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]

_FONT_NAME = "Helvetica"  # 폴백: 내장 폰트
for _fp in _FONT_PATHS:
    if os.path.exists(_fp):
        try:
            pdfmetrics.registerFont(TTFont("AppleGothic", _fp))
            _FONT_NAME = "AppleGothic"
        except Exception:
            pass
        break

_settings = Settings()
_llm = ChatOpenAI(
    model=_settings.model_name,
    api_key=_settings.openai_api_key,
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
    final_report = report.strip()

    # ── 파일 저장 ────────────────────────────────────────────────────────────
    docs_dir = Path(__file__).resolve().parents[2] / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path  = docs_dir / f"report_{timestamp}.md"
    pdf_path = docs_dir / f"report_{timestamp}.pdf"

    # 마크다운 저장
    md_path.write_text(final_report, encoding="utf-8")

    # PDF 저장
    _save_pdf(final_report, pdf_path)

    return {
        "final_report":    final_report,
        "report_md_path":  str(md_path),
        "report_pdf_path": str(pdf_path),
    }


# ---------------------------------------------------------------------------
# PDF 변환 헬퍼
# ---------------------------------------------------------------------------

def _save_pdf(markdown_text: str, pdf_path: Path) -> None:
    """마크다운 텍스트를 PDF로 변환하여 저장한다."""
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    fn = _FONT_NAME

    style_h1 = ParagraphStyle("h1", fontName=fn, fontSize=18, spaceAfter=6, spaceBefore=12, leading=22)
    style_h2 = ParagraphStyle("h2", fontName=fn, fontSize=14, spaceAfter=4, spaceBefore=10, leading=18)
    style_h3 = ParagraphStyle("h3", fontName=fn, fontSize=12, spaceAfter=3, spaceBefore=8, leading=16)
    style_body = ParagraphStyle("body", fontName=fn, fontSize=10, spaceAfter=4, leading=14)
    style_li   = ParagraphStyle("li",   fontName=fn, fontSize=10, spaceAfter=2, leading=14, leftIndent=12)

    story = []

    for line in markdown_text.splitlines():
        stripped = line.rstrip()

        if stripped.startswith("### "):
            story.append(Paragraph(stripped[4:], style_h3))
        elif stripped.startswith("## "):
            story.append(Paragraph(stripped[3:], style_h2))
        elif stripped.startswith("# "):
            story.append(Paragraph(stripped[2:], style_h1))
        elif stripped == "---":
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4))
        elif stripped.startswith("| "):
            # 구분선 행(| --- |) 스킵
            if re.match(r"^\|[\s\-|]+\|$", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            text = "  |  ".join(
                re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", c) for c in cells
            )
            story.append(Paragraph(text, style_body))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped[2:])
            story.append(Paragraph(f"• {text}", style_li))
        elif stripped == "":
            story.append(Spacer(1, 4))
        else:
            text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped)
            story.append(Paragraph(text, style_body))

    doc.build(story)


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
        "report_md_path":    "",
        "report_pdf_path":   "",
    })

    return {
        "final_report":    result["final_report"],
        "report_md_path":  result["report_md_path"],
        "report_pdf_path": result["report_pdf_path"],
    }
