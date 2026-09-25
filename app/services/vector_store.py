from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings


class VectorStoreService:
    """
    Service for generating vector embeddings locally via SentenceTransformers 
    and managing Qdrant vector database operations.
    """

    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        # Load local embedding model (downloads automatically on first run)
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """
        Create Qdrant collection if it does not already exist.
        """
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]

        if settings.COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=settings.VECTOR_DIMENSION,
                    distance=models.Distance.COSINE
                )
            )

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings locally for a list of text strings.
        """
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Generate embeddings for chunks and batch upsert points into Qdrant.
        """
        if not chunks:
            return 0

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)

        points = []
        for idx, chunk in enumerate(chunks):
            point = models.PointStruct(
                id=chunk["chunk_id"],
                vector=embeddings[idx],
                payload={
                    "text": chunk["text"],
                    "token_count": chunk["token_count"],
                    "chunk_index": chunk["index"],
                    "metadata": chunk.get("metadata", {})
                }
            )
            points.append(point)

        self.client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=points
        )
        return len(points)