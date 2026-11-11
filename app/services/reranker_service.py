from typing import List, Dict, Any
from sentence_transformers import CrossEncoder


class RerankerService:
    """
    Service using a local Cross-Encoder model to rescore and rerank candidate text chunks.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        # Loads local CPU-friendly Cross-Encoder model (downloads automatically on first run ~80MB)
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Score (query, chunk) pairs and return top_k candidates sorted by relevance score.
        """
        if not candidate_chunks:
            return []

        # Form (query, document_text) pairs for Cross-Encoder
        pairs = [[query, chunk["text"]] for chunk in candidate_chunks]
        scores = self.model.predict(pairs)

        reranked_list = []
        for idx, score in enumerate(scores):
            item = candidate_chunks[idx].copy()
            item["relevance_score"] = round(float(score), 4)
            reranked_list.append(item)

        # Sort by Cross-Encoder score in descending order
        reranked_list.sort(key=lambda x: x["relevance_score"], reverse=True)
        return reranked_list[:top_k]