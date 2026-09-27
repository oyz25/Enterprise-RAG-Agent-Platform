from typing import List, Dict, Any, Optional
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

    def search_similarity(
        self, 
        query_text: str, 
        limit: int = 3, 
        filename_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert query text to embedding vector and perform cosine similarity search in Qdrant.
        Handles API compatibility across different qdrant-client versions.
        """
        query_vector = self.generate_embeddings([query_text])[0]

        query_filter = None
        if filename_filter:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.filename",
                        match=models.MatchValue(value=filename_filter)
                    )
                ]
            )

        # Compatibility wrapper for newer and older qdrant-client versions
        if hasattr(self.client, "query_points"):
            search_result = self.client.query_points(
                collection_name=settings.COLLECTION_NAME,
                query=query_vector,
                query_filter=query_filter,
                limit=limit
            ).points
        elif hasattr(self.client, "search"):
            search_result = self.client.search(
                collection_name=settings.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )
        else:
            search_result = self.client.search_points(
                collection_name=settings.COLLECTION_NAME,
                vector=query_vector,
                filter=query_filter,
                limit=limit
            ).points

        results = []
        for hit in search_result:
            results.append({
                "chunk_id": str(hit.id),
                "score": round(float(hit.score), 4),
                "text": hit.payload.get("text", ""),
                "chunk_index": hit.payload.get("chunk_index", 0),
                "token_count": hit.payload.get("token_count", 0),
                "metadata": hit.payload.get("metadata", {})
            })
        return results