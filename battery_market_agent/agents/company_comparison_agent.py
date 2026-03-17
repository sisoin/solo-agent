"""
회사 비교 에이전트

역할:
    LG에너지솔루션, CATL 각각의 기업 분석 에이전트(company_analysis_agent)가
    병렬로 완료된 후 두 결과를 받아 비교 분석을 수행한다.

입력:
    state["company_report"]["LG에너지솔루션"]: LG에너지솔루션 기업 분석 결과
    state["company_report"]["CATL"]          : CATL 기업 분석 결과

출력:
    state["comparison_report"]: 5개 차원 비교 분석 결과 (한국어, 구조화 텍스트)

비교 차원:
    1. 기술 전략 (배터리 화학, 폼팩터, 차세대 기술)
    2. 지역 전략 (중국·유럽·북미 포지셔닝)
    3. 고객 전략 (OEM 파트너십, 고객 다변화)
    4. 원가 전략 (수직계열화, 공정 효율화)
    5. 신사업 전략 (ESS, 배터리 재활용, 소재)
"""
from langchain_openai import ChatOpenAI

from battery_market_agent.config import Settings
from battery_market_agent.state import BatteryMarketState

# ---------------------------------------------------------------------------
# 비교 평가 기준
# 각 차원에서 두 기업을 비교할 때 확인해야 할 구체적 평가 포인트.
# _COMPARISON_PROMPT에 주입되어 비교 깊이와 일관성을 높인다.
# ---------------------------------------------------------------------------

COMPARISON_CRITERIA = {
    "tech": (
        "배터리 화학 포트폴리오(NCM 고니켈·NCMA·LFP) 비중 및 전환 대응 속도, "
        "파우치·각형·원통형(4680) 폼팩터 전략 차이, "
        "셀 에너지 밀도(Wh/kg) 수치 비교, "
        "전고체 배터리 개발 단계(연구·시제품·파일럿·양산 로드맵) 비교, "
        "특허 포트폴리오 규모 및 핵심 기술 영역 차이"
    ),
    "region": (
        "중국 현지 생산능력(GWh)·중국 OEM 고객 비중, "
        "유럽 기가팩토리 투자 규모·일정·고객 확보 현황, "
        "북미 IRA 세액공제(AMPC) 수혜 규모·현지 JV 현황, "
        "신흥 시장(동남아·인도·중동) 진출 계획, "
        "단일 지역 매출 편중 리스크 비교"
    ),
    "customer": (
        "tier-1 OEM 고객사 수 및 다양성, "
        "최대 단일 고객사 매출 집중도(%), "
        "신규 수주 파이프라인 규모(GWh·$B), "
        "비차량(ESS·선박·항공) 고객 비중, "
        "장기 공급 계약 비중 및 평균 계약 기간"
    ),
    "cost": (
        "셀 제조 원가($/kWh) 수치 비교, "
        "수직계열화 수준(원자재 조달→소재→셀→팩 통합 정도), "
        "원자재 장기 구매 계약·광산 지분 확보율, "
        "건식 전극·AI 수율 관리 등 공정 혁신 도입 여부, "
        "영업이익률 추이 및 경쟁사 대비 수익성 격차"
    ),
    "new_biz": (
        "ESS 매출 비중 및 연간 성장률, "
        "배터리 재활용·2nd Life 사업 단계(계획·파일럿·상용화), "
        "양극재·음극재 소재 자체 생산 투자 규모, "
        "BMS 소프트웨어·에너지 플랫폼 등 비(非)셀 사업 확장 현황, "
        "신사업 합산 매출 기여도 및 성장 전망"
    ),
}

_settings = Settings()
_llm = ChatOpenAI(
    model=_settings.model_name,
    api_key=_settings.openai_api_key,
)

_COMPARISON_PROMPT = """\
당신은 배터리 기업 전략 비교 분석 전문가입니다.
두 기업의 분석 보고서를 바탕으로 아래 5개 차원에서 비교 분석을 수행하세요.

## 비교 차원 및 평가 기준

1. **기술 전략**
   평가 기준: {tech}

2. **지역 전략**
   평가 기준: {region}

3. **고객 전략**
   평가 기준: {customer}

4. **원가 전략**
   평가 기준: {cost}

5. **신사업 전략**
   평가 기준: {new_biz}

## 작성 지침

- 각 차원마다 두 기업의 차이점과 강약점을 구체적으로 서술하세요.
- 수치·데이터가 있으면 반드시 인용하세요.
- 한 기업의 우위만 서술하지 말고, 각 차원에서 양사의 강점과 한계를 모두 포함하세요.
- 마지막에 **종합 시사점** (투자·파트너십 관점)을 포함하세요.
- 한국어로 구조화된 보고서 형식으로 작성하세요.

---

=== LG에너지솔루션 분석 보고서 ===
{{lg_report}}

=== CATL 분석 보고서 ===
{{catl_report}}
""".format(**COMPARISON_CRITERIA)


def company_comparison_agent(state: BatteryMarketState) -> dict:
    """
    회사 비교 에이전트 노드.

    company_report의 두 기업 분석 결과를 LLM에 전달하여
    5개 차원 비교 분석을 수행하고 comparison_report에 저장한다.
    """
    company_report = state.get("company_report", {})
    lg_report   = company_report.get("LG에너지솔루션", "분석 결과 없음")
    catl_report = company_report.get("CATL", "분석 결과 없음")

    prompt = _COMPARISON_PROMPT.format(
        lg_report=lg_report,
        catl_report=catl_report,
    )

    result = _llm.invoke(prompt)
    return {"comparison_report": result.content}
