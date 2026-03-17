"""
SWOT 서브그래프 노드 모음.

노드 흐름:
    gather_info_node   → 뉴스·웹 검색으로 원시 정보 수집
    classify_swot_node → LLM 구조화 출력으로 S/W/O/T 분류
    format_matrix_node → analyze_swot 툴로 2×2 행렬 렌더링
"""
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

from battery_market_agent.config.settings import Settings
from battery_market_agent.tools.search_tools import fetch_google_news, search_web
from battery_market_agent.tools.analysis_tools import analyze_swot
from .state import SWOTState

_settings = Settings()
_llm = ChatAnthropic(
    model=_settings.model_name,
    api_key=_settings.anthropic_api_key,
)


# ---------------------------------------------------------------------------
# 구조화 출력 스키마
# ---------------------------------------------------------------------------

class SWOTItems(BaseModel):
    """LLM이 원시 정보로부터 분류한 SWOT 항목."""
    strengths: list[str] = Field(description="내부 강점 항목 목록 (경쟁 우위, 잘하고 있는 것)")
    weaknesses: list[str] = Field(description="내부 약점 항목 목록 (부족한 점, 개선 필요 부분)")
    opportunities: list[str] = Field(description="외부 기회 항목 목록 (유리하게 작용하는 환경 요소)")
    threats: list[str] = Field(description="외부 위협 항목 목록 (위험 요소)")


_structured_llm = _llm.with_structured_output(SWOTItems)


# ---------------------------------------------------------------------------
# 노드
# ---------------------------------------------------------------------------

def gather_info_node(state: SWOTState) -> dict:
    """
    분석 대상에 대한 최신 뉴스와 웹 검색 결과를 수집합니다.

    - fetch_google_news : 최신 뉴스 기사 (외부 환경 파악 → O/T)
    - search_web        : 시장 동향, 경쟁사 분석, 전략 정보 (S/W/O/T 전반)
    """
    subject = state["subject"]

    news = fetch_google_news.invoke({"query": subject, "period": "1m", "max_results": 10})
    web  = search_web.invoke({"query": f"{subject} 강점 약점 시장 분석", "max_results": 5})

    return {"raw_info": [news, web]}


def classify_swot_node(state: SWOTState) -> dict:
    """
    수집된 원시 정보를 LLM 구조화 출력으로 S/W/O/T 항목으로 분류합니다.
    """
    subject  = state["subject"]
    raw_text = "\n\n---\n\n".join(state["raw_info"])

    prompt = f"""다음은 '{subject}'에 관해 수집된 정보입니다.

{raw_text}

위 정보를 바탕으로 '{subject}'의 SWOT 분석을 수행하세요.
- Strengths (강점)    : 내부적으로 잘하고 있는 것, 경쟁 우위 요소
- Weaknesses (약점)   : 내부적으로 부족한 점, 개선이 필요한 부분
- Opportunities (기회): 외부 환경에서 유리하게 작용하는 요소
- Threats (위협)      : 외부 환경에서의 위험 요소

각 항목은 구체적이고 간결하게 작성하세요."""

    result: SWOTItems = _structured_llm.invoke(prompt)

    return {
        "strengths":     result.strengths,
        "weaknesses":    result.weaknesses,
        "opportunities": result.opportunities,
        "threats":       result.threats,
    }


def format_matrix_node(state: SWOTState) -> dict:
    """
    분류된 S/W/O/T 항목을 analyze_swot 툴로 2×2 행렬 문자열로 렌더링합니다.
    """
    matrix = analyze_swot.invoke({
        "subject":       state["subject"],
        "strengths":     state["strengths"],
        "weaknesses":    state["weaknesses"],
        "opportunities": state["opportunities"],
        "threats":       state["threats"],
    })
    return {"swot_matrix": matrix}
