"""배터리 시장 전략 분석 에이전트 진입점."""
from battery_market_agent.config import Settings
from battery_market_agent.agents import build_graph


def run(query: str) -> dict:
    settings = Settings()
    graph = build_graph()

    # TODO: BatteryMarketState 정의 후 실제 초기 상태로 교체
    initial_state = {"query": query}

    result = graph.invoke(initial_state)
    return result


if __name__ == "__main__":
    output = run("2025년 글로벌 배터리 시장에서 LFP vs NCM 전략 분석")
    print(output)
