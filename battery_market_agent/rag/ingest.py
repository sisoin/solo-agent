"""
PDF 인제스트 스크립트.

사용법:
    uv run python -m battery_market_agent.rag.ingest
"""
from pathlib import Path
from battery_market_agent.rag.retriever import BatteryRAG

PDF_FILES = [
    Path(__file__).parents[2] / "12.pdf",
    Path(__file__).parents[2] / "123.pdf",
]


def main() -> None:
    rag = BatteryRAG()

    all_docs = []
    for pdf_path in PDF_FILES:
        if not pdf_path.exists():
            print(f"[경고] 파일을 찾을 수 없습니다: {pdf_path}")
            continue
        print(f"[ingest] 로딩 중: {pdf_path.name}")
        docs = rag.load_documents(str(pdf_path))
        all_docs.extend(docs)
        print(f"         → {len(docs)}페이지 로딩 완료")

    if not all_docs:
        print("[ingest] 인덱싱할 문서가 없습니다.")
        return

    print(f"[ingest] 총 {len(all_docs)}페이지를 Qdrant에 인덱싱합니다...")
    rag.build_index(all_docs)
    print("[ingest] 완료")


if __name__ == "__main__":
    main()
