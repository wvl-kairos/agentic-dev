from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Cerebro Intelligence Fabric"
    env: str = "development"
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    backend_port: int = 8000

    # Neo4j
    neo4j_uri: str = ""
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""

    # OpenAI (embeddings)
    openai_api_key: str = ""

    # Anthropic (agent reasoning)
    anthropic_api_key: str = ""

    # RAG (ChromaDB + BM25 hybrid)
    chromadb_persist_dir: str = "./chroma_data"
    embedding_model: str = "text-embedding-3-small"
    rag_top_k: int = 5
    rag_rrf_k: int = 60
    rag_max_chunk_size: int = 800

    # Query
    retrieval_top_k: int = 10
    max_context_tokens: int = 4000

    # Agents
    agent_model: str = "claude-sonnet-4-20250514"
    agent_max_tokens: int = 4096
    agent_temperature: float = 0.3

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def neo4j_enabled(self) -> bool:
        return bool(self.neo4j_uri)

    class Config:
        env_file = ("../.env", ".env")


settings = Settings()
