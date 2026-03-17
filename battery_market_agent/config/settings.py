from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    model_name: str = "claude-sonnet-4-6"

    # RAG / 벡터 저장소
    vector_store_path: str = "./data/vectorstore"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
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
