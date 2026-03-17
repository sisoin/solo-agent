"""배터리 시장 전략 분석 에이전트 진입점."""
import asyncio

from battery_market_agent.agents import build_graph


async def run(query: str) -> dict:
    graph = build_graph()
    result = await graph.ainvoke({"query": query})
    return result


if __name__ == "__main__":
    output = asyncio.run(run("LG에너지솔루션 vs CATL 배터리 전략 비교 분석"))
    print("PDF 저장 경로:", output.get("report_pdf_path", ""))
    print("\n[SUMMARY]")
    print(output.get("final_report", ""))
