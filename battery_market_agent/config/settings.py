from pydantic_settings import BaseSettings
from langchain_core.rate_limiters import InMemoryRateLimiter

# 보고서 생성(gpt-4o) 전용 rate limiter
# TPM 30,000 기준: 1호출 ≈ 4,000~5,000 토큰 → 분당 6회 → 초당 0.1회
shared_rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,
    check_every_n_seconds=0.1,
    max_bucket_size=2,
)

# 분석 에이전트(gpt-4o-mini) 전용 rate limiter
# TPM 200,000 기준: 1호출 ≈ 3,000~4,000 토큰 → 분당 50회 → 초당 0.5회
analysis_rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,
    check_every_n_seconds=0.05,
    max_bucket_size=5,
)


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    model_name: str = "gpt-4o"           # 보고서 생성 에이전트용
    analysis_model_name: str = "gpt-4o-mini"  # 분석 에이전트용

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
