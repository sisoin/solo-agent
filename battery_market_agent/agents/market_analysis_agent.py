"""
시장 분석 에이전트

역할:
    웹 서치 도구(search_web, fetch_google_news)를 활용해
    대상 기업의 최신 배터리 시장 동향을 수집·분석한다.

수집 대상:
    - 글로벌 배터리 시장 규모 및 성장률
    - 주요 지역별 수요 동향 (중국, 유럽, 북미)
    - 원자재 가격 동향 (리튬, 코발트, 니켈)
    - 최신 뉴스 및 산업 이슈

입력:
    state["company"]: 분석 대상 회사명

출력:
    state["market_trends"][company]: 시장 동향 분석 결과 문자열
"""
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from battery_market_agent.config.settings import Settings
from battery_market_agent.state import BatteryMarketState
from battery_market_agent.tools import search_web, fetch_google_news, fetch_price_trends

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

_settings = Settings()
_llm = ChatAnthropic(
    model=_settings.model_name,
    api_key=_settings.anthropic_api_key,
)

MARKET_TOOLS = [search_web, fetch_google_news, fetch_price_trends]

SYSTEM_PROMPT = """당신은 배터리 산업 전문 시장 분석가입니다.
주어진 기업에 대해 다음 항목을 반드시 조사하고 분석 결과를 반환하세요.

조사 항목:
1. 글로벌 배터리 시장 규모 및 성장률 (최신 데이터)
2. 해당 기업의 시장 점유율 및 포지셔닝
3. 주요 지역별 수요 동향 (중국, 유럽, 북미)
4. 배터리 원자재 가격 동향 (리튬, 코발트, 니켈)
5. 최신 뉴스 및 산업 이슈

지침:
- search_web과 fetch_google_news 툴을 적극적으로 활용하세요.
- 각 항목마다 출처가 되는 검색을 수행한 뒤 결과를 종합하세요.
- 최종 답변은 항목별로 구조화된 한국어 분석 보고서 형식으로 작성하세요.
"""

# 모듈 로드 시 에이전트를 한 번만 컴파일
# name 파라미터: create_supervisor가 핸드오프 도구 이름으로 사용 (transfer_to_market_analysis_agent)
_agent = create_react_agent(
    model=_llm,
    tools=MARKET_TOOLS,
    prompt=SYSTEM_PROMPT,
    name="market_analysis_agent",
)

# ---------------------------------------------------------------------------
# 노드
# ---------------------------------------------------------------------------

def market_analysis_agent(state: BatteryMarketState) -> dict:
    """
    시장 분석 에이전트 노드.

    create_react_agent로 빌드된 ReAct 루프를 실행하여
    웹 검색 결과를 기반으로 배터리 시장 동향을 수집·분석한다.
    """
    company = state["company"]

    result = _agent.invoke({
        "messages": [
            ("user", f"{company}의 현재 배터리 시장 동향을 위 항목에 따라 분석해주세요.")
        ]
    })

    market_trends = state.get("market_trends", {})
    market_trends[company] = result["messages"][-1].content

    return {"market_trends": market_trends}
