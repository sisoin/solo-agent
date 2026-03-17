"""
보고서 생성 에이전트

처리 흐름:
    1. generate_sections_node : LLM.with_structured_output → ReportSections
    2. render_html_node       : ReportSections → HTML 문자열 (인라인 CSS 포함)
    3. convert_pdf_node       : weasyprint HTML → PDF 저장
"""
import re
from datetime import datetime
from pathlib import Path

import requests
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import weasyprint

from battery_market_agent.config import Settings
from battery_market_agent.state.report_state import ReportState, ReportSections

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
_settings = Settings()
_llm = ChatOpenAI(model=_settings.model_name, api_key=_settings.openai_api_key)
_structured_llm = _llm.with_structured_output(ReportSections)

_SYSTEM_PROMPT = """\
당신은 배터리 산업 전략 분석 전문가입니다.
수집된 분석 정보를 바탕으로 아래 규칙을 준수하여 전략 분석 보고서를 작성하세요.

보고서 작성 규칙:
1. SUMMARY (맨 앞, 1/2페이지 이내)
   - 전체 보고서의 핵심 인사이트 요약 (개요 장표 아님), 200자 내외

2. 본문 필수 포함 항목 및 분량 기준
   ※ 각 항목은 아래 최소 분량을 반드시 충족하세요. 수치·사례·근거를 구체적으로 포함할수록 좋습니다.

   [1장 시장 배경] — 항목당 400자 이상
   - 1.1 시장 현황·규모 : 달러 규모, CAGR, 성장 드라이버 수치 포함, 3문단 이상
   - 1.2 시장 구조 변화 : LFP·NCM 점유율 변화, 전고체·ESS 동향 등 3개 이상 트렌드
   - 1.3 경쟁 구도      : Top 5 점유율 수치, CATL·LGES 포지션 비교, 3문단 이상

   [2장 기업별 포트폴리오] — 항목당 400자 이상
   - LG에너지솔루션 포트폴리오 : 폼팩터별 비중, 고객사·JV 현황, 3문단 이상
   - LG에너지솔루션 기술       : NCM·NCMA·건식전극·전고체 로드맵, 3문단 이상
   - CATL 포트폴리오           : LFP·NCM·나트륨이온 라인업, 고객사·해외공장, 3문단 이상
   - CATL 기술                 : CTP·기린배터리·나트륨이온·원가 공정 혁신, 3문단 이상

   [3장 전략 비교·SWOT] — 현행 유지 (표 형식)
   - 전략 비교표 5개 항목 (기술·지역·고객·원가·신사업)
   - SWOT: 내부(S/W) + 외부(O/T) 구분, 각 항목 2문장 이상

   [4장 종합 시사점] — 항목당 350자 이상
   - 4.1 포지셔닝 차이  : 지역·화학·고객 3축 비교, 수치 포함
   - 4.2 시장 전망      : 2025~2030 전망, 기회·리스크 균형 서술
   - 4.3 투자·협력 의견 : 투자 매력도·리스크·협력 가능 영역, 2문단 이상

3. REFERENCE (맨 마지막)
   - 반드시 아래 [수집된 출처 목록]에 있는 자료만 기재하세요.
   - 목록에 없는 URL을 추측하거나 임의로 생성하지 마세요.
   - 웹페이지·뉴스·기관 보고서 등 온라인 자료는 URL을 반드시 포함하세요.
     URL이 [수집된 출처 목록]에 없으면 해당 자료는 기재하지 마세요.
   - URL이 원천적으로 없는 자료(오프라인 PDF, 학술지 논문 등)만 URL 없이 작성하세요.
   - 기관 보고서 : 발행기관(YYYY). 보고서명. URL
   - 학술 논문  : 저자(YYYY). 논문제목. 학술지명, 권(호), 페이지.
   - 웹페이지   : 기관명 또는 작성자(YYYY-MM-DD). 제목. URL

모든 내용은 한국어로 작성하고, 수치와 근거를 구체적으로 포함하세요.
"""

# ---------------------------------------------------------------------------
# 노드 1: 섹션 생성
# ---------------------------------------------------------------------------

def generate_sections_node(state: ReportState) -> dict:
    # 실제 수집된 출처 목록을 컨텍스트에 포함
    market_sources = state.get("market_sources", {})
    source_lines = []
    for company, sources in market_sources.items():
        for s in sources:
            url = s.get("url", "")
            title = s.get("title", "")
            if url:
                source_lines.append(f"- [{company}] {title} | {url}" if title else f"- [{company}] {url}")

    sources_block = (
        "\n\n[수집된 출처 목록 — REFERENCE는 이 목록에 있는 URL만 사용]\n"
        + "\n".join(source_lines)
        if source_lines else ""
    )

    context = "\n\n".join([
        "=== 기업별 분석 보고서 ===",
        *[f"[{c}]\n{r}" for c, r in state.get("company_report", {}).items()],
        "=== 비교 분석 보고서 (SWOT 포함) ===",
        state.get("comparison_report", ""),
    ]) + sources_block

    prompt = f"{_SYSTEM_PROMPT}\n\n{context}"
    sections: ReportSections = _structured_llm.invoke(prompt)
    return {"sections": sections}


# ---------------------------------------------------------------------------
# 노드 1-b: 참고문헌 URL 유효성 검사
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+")


def _check_url(url: str, timeout: int = 5) -> bool:
    """HEAD 요청으로 URL 유효성 확인. 400 미만 응답이면 유효."""
    try:
        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        return resp.status_code < 400
    except Exception:
        return False


def validate_references_node(state: ReportState) -> dict:
    """sections.references의 URL을 HTTP 요청으로 검증하고 유효하지 않은 항목을 제거한다."""
    sections: ReportSections = state["sections"]
    valid_refs: list[str] = []
    for ref in sections.references:
        urls = _URL_RE.findall(ref)
        if not urls:
            # URL 없는 항목(논문 등)은 그대로 유지
            valid_refs.append(ref)
            continue
        if all(_check_url(url) for url in urls):
            valid_refs.append(ref)
        else:
            print(f"[validate_references] 유효하지 않은 URL 제거: {ref[:80]}")

    sections.references = valid_refs
    return {"sections": sections}


# ---------------------------------------------------------------------------
# 노드 2: HTML 렌더링
# ---------------------------------------------------------------------------

_HTML_CSS = """\
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    font-size: 10pt;
    color: #1a1a2e;
    line-height: 1.6;
    padding: 20mm;
}

/* 제목 */
.report-title { font-size: 22pt; font-weight: 700; color: #1a1a2e; margin-bottom: 4pt; }
.report-subtitle { font-size: 12pt; color: #4a4a6a; margin-bottom: 16pt; }
.divider { border: none; border-top: 2px solid #2d2d5e; margin: 12pt 0; }
.section-divider { border: none; border-top: 0.5px solid #ccccdd; margin: 14pt 0; }

/* 섹션 제목 */
h1 { font-size: 14pt; font-weight: 700; color: #1a1a2e; margin: 16pt 0 6pt; }
h2 { font-size: 12pt; font-weight: 700; color: #2d2d5e; margin: 12pt 0 4pt; }
h3 { font-size: 10pt; font-weight: 700; color: #3a3a7e; margin: 10pt 0 3pt; }

/* 본문 */
p { margin-bottom: 6pt; }

/* SUMMARY 박스 */
.summary-box {
    background: #f5f5ff;
    border-left: 4px solid #2d2d5e;
    padding: 10pt 12pt;
    margin: 8pt 0 16pt;
    font-size: 10pt;
}

/* 공통 표 스타일 */
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; font-size: 9pt; }
th { background: #2d2d5e; color: #ffffff; font-weight: 700; padding: 6pt 8pt; text-align: left; }
td { padding: 6pt 8pt; vertical-align: top; border: 0.5px solid #ccccdd; }
tr:nth-child(even) td { background: #f9f9ff; }

/* 전략 비교표 - 첫 열 강조 */
.strategy-table td:first-child { background: #eeeef8; font-weight: 700; width: 18%; }

/* SWOT 표 */
.swot-s td, .swot-w td { background: #e8f4e8; }
.swot-o td, .swot-t td { background: #f4e8e8; }
.swot-table td:first-child { font-weight: 700; width: 8%; text-align: center; }
.swot-table td:nth-child(2) { width: 28%; }

/* 참고문헌 */
.ref-list { font-size: 8.5pt; color: #333; }
.ref-list li { margin-bottom: 4pt; list-style: disc; margin-left: 16pt; }

/* 페이지 나눔 방지 */
.keep-together { page-break-inside: avoid; }
"""


def _p(text: str) -> str:
    """문단 텍스트를 <p> 태그로 감싼다. 빈 줄 기준으로 분리."""
    return "".join(f"<p>{para.strip()}</p>" for para in text.split("\n\n") if para.strip())


def _strategy_table(s: ReportSections) -> str:
    rows = [
        ("기술 방향성", s.strategy_tech),
        ("지역 전략",   s.strategy_region),
        ("고객 전략",   s.strategy_customer),
        ("원가 전략",   s.strategy_cost),
        ("신사업 방향", s.strategy_new_biz),
    ]
    trs = "".join(
        f"<tr><td>{label}</td><td>{row.lg}</td><td>{row.catl}</td></tr>"
        for label, row in rows
    )
    return f"""
<table class="strategy-table keep-together">
  <thead><tr><th>전략 항목</th><th>LG에너지솔루션</th><th>CATL</th></tr></thead>
  <tbody>{trs}</tbody>
</table>"""


def _swot_table(swot, company: str) -> str:
    rows = [
        ("S", "강점 (Strength)<br>내부 경쟁 우위 요소",    swot.strength,    "swot-s"),
        ("W", "약점 (Weakness)<br>내부 개선 필요 부분",    swot.weakness,    "swot-w"),
        ("O", "기회 (Opportunity)<br>외부 유리 환경 요소", swot.opportunity, "swot-o"),
        ("T", "위협 (Threat)<br>외부 위험 요소",           swot.threat,      "swot-t"),
    ]
    trs = "".join(
        f'<tr class="{css}"><td>{code}</td><td>{label}</td><td>{content}</td></tr>'
        for code, label, content, css in rows
    )
    return f"""
<table class="swot-table keep-together">
  <thead><tr><th>구분</th><th>항목</th><th>내용</th></tr></thead>
  <tbody>{trs}</tbody>
</table>"""


def render_html_node(state: ReportState) -> dict:
    s: ReportSections = state["sections"]

    refs_html = "".join(f"<li>{r}</li>" for r in s.references)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>{_HTML_CSS}</style>
</head>
<body>

<p class="report-title">배터리 기업 전략 분석 보고서</p>
<p class="report-subtitle">CATL vs LG에너지솔루션</p>
<hr class="divider">

<h1>SUMMARY</h1>
<div class="summary-box">{s.summary}</div>
<hr class="section-divider">

<h1>1. 시장 배경 : 글로벌 배터리 시장 환경 변화</h1>

<h2>1.1 글로벌 배터리 시장 현황 및 규모</h2>
{_p(s.market_overview)}

<h2>1.2 시장 구조 변화 및 핵심 트렌드</h2>
{_p(s.market_trends)}

<h2>1.3 경쟁 구도 개요</h2>
{_p(s.competitive_landscape)}
<hr class="section-divider">

<h1>2. 기업별 포트폴리오 다각화 전략 및 핵심 경쟁력</h1>

<h2>2.1 LG에너지솔루션</h2>
<h3>2.1.1 사업 포트폴리오 구성</h3>
{_p(s.lg_portfolio)}
<h3>2.1.2 기술 경쟁력</h3>
{_p(s.lg_tech)}

<h2>2.2 CATL</h2>
<h3>2.2.1 사업 포트폴리오 구성</h3>
{_p(s.catl_portfolio)}
<h3>2.2.2 기술 경쟁력</h3>
{_p(s.catl_tech)}
<hr class="section-divider">

<h1>3. 핵심 전략 비교 및 SWOT 분석</h1>

<h2>3.1 핵심 전략 비교</h2>
{_strategy_table(s)}

<h2>3.2 SWOT 분석</h2>

<h3>3.2.1 LG에너지솔루션 SWOT</h3>
{_swot_table(s.swot_lg, "LG에너지솔루션")}

<h3>3.2.2 CATL SWOT</h3>
{_swot_table(s.swot_catl, "CATL")}

<h3>3.2.3 SWOT 비교 시사점</h3>
<p><strong>내부 역량 (S/W) 관점</strong></p>
{_p(s.swot_sw_implications)}
<p><strong>외부 환경 (O/T) 관점</strong></p>
{_p(s.swot_ot_implications)}
<hr class="section-divider">

<h1>4. 종합 시사점</h1>

<h2>4.1 두 기업의 전략적 포지셔닝 차이</h2>
{_p(s.positioning_diff)}

<h2>4.2 배터리 시장 향후 전망과 시사점</h2>
{_p(s.market_outlook)}

<h2>4.3 투자·협력 관점 종합 의견</h2>
{_p(s.investment_opinion)}
<hr class="section-divider">

<h1>REFERENCE</h1>
<ul class="ref-list">{refs_html}</ul>

</body>
</html>"""

    return {"final_report": html}


# ---------------------------------------------------------------------------
# 노드 3: weasyprint HTML → PDF
# ---------------------------------------------------------------------------

def convert_pdf_node(state: ReportState) -> dict:
    html = state["final_report"]

    docs_dir = Path(__file__).resolve().parents[2] / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path  = docs_dir / f"report_{timestamp}.pdf"

    weasyprint.HTML(string=html).write_pdf(str(pdf_path))
    print(f"[report_generation_agent] PDF 저장: {pdf_path}")

    return {"report_pdf_path": str(pdf_path)}


# ---------------------------------------------------------------------------
# 서브그래프
# ---------------------------------------------------------------------------

def build_report_graph():
    graph = StateGraph(ReportState)
    graph.add_node("generate_sections",    generate_sections_node)
    graph.add_node("validate_references",  validate_references_node)
    graph.add_node("render_html",          render_html_node)
    graph.add_node("convert_pdf",          convert_pdf_node)

    graph.set_entry_point("generate_sections")
    graph.add_edge("generate_sections",   "validate_references")
    graph.add_edge("validate_references", "render_html")
    graph.add_edge("render_html",         "convert_pdf")
    graph.add_edge("convert_pdf",         END)

    return graph.compile()


_report_graph = build_report_graph()


def report_generation_agent(state) -> dict:
    result = _report_graph.invoke({
        "company_report":    state.get("company_report", {}),
        "comparison_report": state.get("comparison_report", ""),
        "market_sources":    state.get("market_sources", {}),
        "sections":          None,
        "final_report":      "",
        "report_pdf_path":   "",
    })
    return {
        "final_report":    result["final_report"],
        "report_pdf_path": result["report_pdf_path"],
    }
