"""
PDF 및 URL 인제스트 스크립트.

사용법:
    uv run python -m battery_market_agent.rag.ingest
"""
from pathlib import Path
from battery_market_agent.rag.retriever import BatteryRAG

_DATA_DIR = Path(__file__).parents[2] / "data" / "tech_docs"

# (디렉터리_경로, company명)
PDF_DIRS = [
    (_DATA_DIR / "LG에너지솔루션", "LG에너지솔루션"),
    (_DATA_DIR / "CATL", "CATL"),
]

# (url, company) — company=None 이면 메타데이터 필터 없이 저장
WEB_SOURCES = [
    ("https://cnevpost.com/2025/02/11/global-ev-battery-market-share-2024/", None),
]


def main() -> None:
    rag = BatteryRAG()

    all_docs = []

    # ── PDF 로딩 ─────────────────────────────────────────────────────────────
    for dir_path, company in PDF_DIRS:
        if not dir_path.exists():
            print(f"[경고] 디렉터리를 찾을 수 없습니다: {dir_path}")
            continue
        pdf_files = list(dir_path.glob("**/*.pdf"))
        if not pdf_files:
            print(f"[경고] PDF 파일 없음: {dir_path}")
            continue
        print(f"[ingest] '{company}' PDF 로딩 중: {dir_path}")
        docs = rag.load_documents(str(dir_path), company=company)
        all_docs.extend(docs)
        print(f"         → {len(docs)}페이지 로딩 완료")

    # ── URL 로딩 ─────────────────────────────────────────────────────────────
    for url, company in WEB_SOURCES:
        print(f"[ingest] URL 로딩 중: {url}")
        docs = rag.load_from_url(url, company=company)
        all_docs.extend(docs)
        print(f"         → {len(docs)}개 문서 로딩 완료")

    if not all_docs:
        print("[ingest] 인덱싱할 문서가 없습니다.")
        return

    print(f"[ingest] 총 {len(all_docs)}개 문서를 Qdrant에 인덱싱합니다...")
    rag.build_index(all_docs)
    print("[ingest] 완료")


if __name__ == "__main__":
    main()
