"""
BatteryRAG — Qdrant 기반 RAG 파이프라인 (싱글톤).

구성:
    - 문서 로딩  : PDFPlumberLoader
    - 텍스트 분할 : RecursiveCharacterTextSplitter
    - 임베딩     : OpenAIEmbeddings (text-embedding-3-small)
    - 벡터 저장소 : QdrantVectorStore (http://localhost:6333)
    - 검색       : 유사도 검색 + 선택적 company 메타데이터 필터

사용:
    rag = BatteryRAG.get_instance()   # 어디서 호출해도 동일 인스턴스 반환
"""
from pathlib import Path
from threading import Lock

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from battery_market_agent.config import Settings


class BatteryRAG:
    """Qdrant 기반 배터리 시장 문서 RAG 파이프라인 (싱글톤)."""

    VECTOR_SIZE = 1536  # text-embedding-3-small 차원

    _instance: "BatteryRAG | None" = None
    _lock: Lock = Lock()

    def __new__(cls, settings: Settings | None = None) -> "BatteryRAG":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls, settings: Settings | None = None) -> "BatteryRAG":
        """싱글톤 인스턴스를 반환한다."""
        return cls(settings)

    def __init__(self, settings: Settings | None = None):
        if self._initialized:
            return
        self._initialized = True
        self.settings = settings or Settings()

        self._embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            api_key=self.settings.openai_api_key,
        )
        self._client = QdrantClient(url=self.settings.qdrant_url)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        self._collection = self.settings.qdrant_collection
        self._ensure_collection()

    # -----------------------------------------------------------------------
    # 내부 유틸
    # -----------------------------------------------------------------------

    def _ensure_collection(self) -> None:
        """컬렉션이 없으면 생성한다."""
        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    def _vector_store(self) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=self._client,
            collection_name=self._collection,
            embedding=self._embeddings,
        )

    # -----------------------------------------------------------------------
    # 공개 API
    # -----------------------------------------------------------------------

    def load_documents(self, source: str, company: str | None = None) -> list[Document]:
        """
        PDF 파일 또는 디렉터리에서 문서를 로딩한다.

        Args:
            source : PDF 파일 경로 또는 PDF가 담긴 디렉터리 경로
            company: 메타데이터에 기록할 회사명 (필터링에 사용)
        """
        path = Path(source)
        pdf_files: list[Path] = []

        if path.is_dir():
            pdf_files = list(path.glob("**/*.pdf"))
        elif path.suffix.lower() == ".pdf":
            pdf_files = [path]
        else:
            raise ValueError(f"지원하지 않는 경로입니다: {source}")

        docs: list[Document] = []
        for pdf_path in pdf_files:
            loader = PDFPlumberLoader(str(pdf_path))
            pages = loader.load()
            for page in pages:
                page.metadata["source"] = str(pdf_path)
                page.metadata["filename"] = pdf_path.name
                if company:
                    page.metadata["company"] = company
            docs.extend(pages)

        return docs

    def build_index(self, documents: list[Document]) -> None:
        """문서를 청크로 분할하고 Qdrant에 임베딩·저장한다."""
        chunks = self._splitter.split_documents(documents)
        self._vector_store().add_documents(chunks)
        print(f"[BatteryRAG] {len(chunks)}개 청크를 '{self._collection}'에 인덱싱 완료")

    def retrieve(self, query: str, company: str | None = None, k: int | None = None) -> list[Document]:
        """
        쿼리에 대한 상위 k개 유사 문서를 반환한다.

        Args:
            query  : 검색 쿼리
            company: 회사명 필터 — None이면 전체 문서에서 검색
            k      : 반환 개수 (기본값: settings.retriever_k)
        """
        k = k or self.settings.retriever_k
        vs = self._vector_store()

        if company:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            qdrant_filter = Filter(
                must=[FieldCondition(key="metadata.company", match=MatchValue(value=company))]
            )
            return vs.similarity_search(query, k=k, filter=qdrant_filter)

        return vs.similarity_search(query, k=k)
