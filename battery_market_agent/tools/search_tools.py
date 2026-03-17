"""
검색 및 문서 로딩 도구 모음.

- fetch_google_news: GoogleNews를 사용한 뉴스 검색
- search_web: TavilySearch를 사용한 웹 검색
- read_pdf: PDFPlumberLoader를 사용한 PDF 읽기
"""
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_community.document_loaders import PDFPlumberLoader
from GoogleNews import GoogleNews


@tool
def fetch_google_news(query: str, period: str = "7d", max_results: int = 10) -> str:
    """
    GoogleNews를 사용해 최신 뉴스 기사를 검색합니다.

    Args:
        query: 검색 키워드
        period: 검색 기간 (예: '7d', '1m') — GoogleNews 형식
        max_results: 최대 결과 수

    Returns:
        뉴스 기사 목록 (제목, 날짜, 링크)
    """
    gn = GoogleNews(lang="ko", period=period)
    gn.search(query)
    results = gn.results(sort=True)[:max_results]

    if not results:
        return f"'{query}'에 대한 뉴스를 찾을 수 없습니다."

    lines = [f"[{i+1}] {r.get('title', '제목 없음')} ({r.get('date', '')})\n    {r.get('link', '')}"
             for i, r in enumerate(results)]
    return "\n".join(lines)


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """
    TavilySearch를 사용해 웹을 검색합니다.

    Args:
        query: 검색 키워드
        max_results: 최대 결과 수

    Returns:
        검색 결과 요약
    """
    search = TavilySearch(
        max_results=max_results,
        # --- 검색 제한 사항 (추후 활성화) ---
        # include_domains=["reuters.com", "bloomberg.com"],
        # exclude_domains=["example.com"],
        # search_depth="advanced",
        # include_answer=True,
    )
    result = search.invoke(query)
    return str(result)


@tool
def read_pdf(file_path: str) -> str:
    """
    PDFPlumberLoader를 사용해 PDF 파일을 읽고 텍스트를 반환합니다.

    Args:
        file_path: PDF 파일의 절대 또는 상대 경로

    Returns:
        PDF 전체 텍스트 내용
    """
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()

    if not docs:
        return f"'{file_path}'에서 내용을 읽을 수 없습니다."

    pages = []
    for i, doc in enumerate(docs):
        pages.append(f"[페이지 {i+1}]\n{doc.page_content.strip()}")
    return "\n\n".join(pages)
