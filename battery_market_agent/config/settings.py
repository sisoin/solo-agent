from pydantic_settings import BaseSettings


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
