from pydantic_settings import BaseSettings
from langchain_core.rate_limiters import InMemoryRateLimiter

# 모든 에이전트가 공유하는 rate limiter — 모듈 로드 시 한 번만 생성
# TPM 30,000 기준: gpt-4o 1호출 ≈ 4,000~5,000 토큰
# → 안전 마진 포함 분당 5회 = 초당 0.08회 (≈ 12초에 1회)
shared_rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.08,
    check_every_n_seconds=0.1,
    max_bucket_size=2,
)


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    model_name: str = "gpt-4o"

    # RAG / 벡터 저장소
    vector_store_path: str = "./data/vectorstore"
    embedding_model: str = "BAAI/bge-m3"
    chunk_size: int = 1500
    chunk_overlap: int = 200
    retriever_k: int = 5

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "battery_docs"

    # 데이터
    data_dir: str = "./data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
