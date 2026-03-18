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
    state["market_sources"][company]: 사용된 출처 목록 [{"title", "url", "tool"}, ...]
"""
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import create_react_agent

from battery_market_agent.config.settings import Settings, analysis_rate_limiter
from battery_market_agent.tools import search_web, fetch_google_news, fetch_price_trends

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

_settings = Settings()
_llm = ChatOpenAI(
    model=_settings.analysis_model_name,
    api_key=_settings.openai_api_key,
    rate_limiter=analysis_rate_limiter,
    max_retries=6,
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

RAG·웹서치 균형 활용 지침:
- 메시지에 [RAG 컨텍스트]가 포함된 경우, 먼저 해당 내용을 검토하여 이미 확보된 정보를 파악하세요.
- RAG 컨텍스트에 있는 내용은 그대로 활용하되, 아래 경우에는 반드시 웹서치로 보완하세요.
  · 시장 규모·성장률 등 수치가 최신(1년 이내)인지 불확실한 경우
  · 원자재 가격처럼 실시간성이 중요한 항목
  · RAG에 없거나 불충분한 항목
- 긍정적 정보(수주·성장·기술 성과)를 검색한 뒤, 반드시 부정적 정보도 별도로 검색하세요.
  예) "{기업} 수주 성장" 검색 → "{기업} 실적 부진 적자 리스크" 추가 검색
- 부정적 측면 예시: 실적 악화, 고객 이탈, 공급망 차질, 가동률 하락, 경쟁사 위협, 소송·리콜, 수익성 압박
- 애널리스트 경고, 신용등급 변화, 규제 리스크도 수집하세요.
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
# 출처 추출
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://[^\s'\"\)\]>,<]+")
_SOURCE_LINE_RE = re.compile(r"^출처:\s*(.+)$", re.MULTILINE)


def _extract_sources(messages: list, tool_name: str) -> list[dict[str, str]]:
    """ToolMessage 내용에서 출처 URL을 파싱한다.

    '출처: <url>' 패턴을 우선 추출하고, 그 외 URL도 수집한다.
    URL이 없거나 http(s)로 시작하지 않는 항목은 제외한다.
    """
    seen: set[str] = set()
    sources: list[dict[str, str]] = []

    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        if msg.name and msg.name != tool_name:
            continue

        content = msg.content if isinstance(msg.content, str) else str(msg.content)

        # '출처: <url>' 패턴 우선 수집 (title은 바로 앞 줄에서 추출)
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            m = _SOURCE_LINE_RE.match(line.strip())
            if m:
                url = m.group(1).strip()
                if url.startswith("http") and url not in seen:
                    # 앞 줄에서 제목 추출: "[N] 제목 (날짜)" 형식
                    title = ""
                    if idx > 0:
                        prev = lines[idx - 1].strip()
                        title_m = re.match(r"^\[\d+\]\s*(.+?)(?:\s*\(.+\))?$", prev)
                        if title_m:
                            title = title_m.group(1).strip()
                    seen.add(url)
                    sources.append({"title": title, "url": url, "tool": tool_name})

        # 위에서 못 잡은 나머지 URL도 수집
        for url in _URL_RE.findall(content):
            if url not in seen:
                seen.add(url)
                sources.append({"title": "", "url": url, "tool": tool_name})

    return sources


