import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Application core settings and environment variable configuration.
    """
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "enterprise_rag_chunks")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384


settings = Settings()