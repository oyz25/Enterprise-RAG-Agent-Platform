from typing import List, Dict, Any, Optional
from app.services.vector_store import VectorStoreService
from app.services.bm25_service import BM25SearchService


class HybridSearchService:
    """
    Engine for fusing Dense Vector Retrieval (Qdrant) and Sparse Keyword Search (BM25)
    using Reciprocal Rank Fusion (RRF).
    """

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.bm25_service = BM25SearchService()

    def reciprocal_rank_fusion(
        self, 
        dense_results: List[Dict[str, Any]], 
        sparse_results: List[Dict[str, Any]], 
        rrf_k: int = 60, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Merge and rerank search results from dense and sparse retrieval engines using RRF algorithm.
        """
        rrf_map: Dict[str, Dict[str, Any]] = {}

        # 1. Process Dense Vector Results
        for rank, item in enumerate(dense_results, start=1):
            doc_id = item["chunk_id"]
            if doc_id not in rrf_map:
                rrf_map[doc_id] = {
                    "chunk_id": doc_id,
                    "rrf_score": 0.0,
                    "dense_rank": rank,
                    "sparse_rank": None,
                    "text": item["text"],
                    "metadata": item.get("metadata", {})
                }
            rrf_map[doc_id]["rrf_score"] += 1.0 / (rrf_k + rank)

        # 2. Process Sparse BM25 Results
        for rank, item in enumerate(sparse_results, start=1):
            doc_id = item["chunk_id"]
            if doc_id not in rrf_map:
                rrf_map[doc_id] = {
                    "chunk_id": doc_id,
                    "rrf_score": 0.0,
                    "dense_rank": None,
                    "sparse_rank": rank,
                    "text": item["text"],
                    "metadata": item.get("metadata", {})
                }
            else:
                rrf_map[doc_id]["sparse_rank"] = rank
            rrf_map[doc_id]["rrf_score"] += 1.0 / (rrf_k + rank)

        # 3. Sort by aggregated RRF score descending
        fused_results = list(rrf_map.values())
        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)

        # Round scores for clean output
        for res in fused_results:
            res["rrf_score"] = round(res["rrf_score"], 6)

        return fused_results[:top_k]

    def search_hybrid(
        self, 
        query: str, 
        top_k: int = 3, 
        rrf_k: int = 60, 
        filename_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute full Hybrid Search pipeline: Dense Search + BM25 Search -> RRF Fusion.
        """
        # Fetch dense vector search candidates
        dense_results = self.vector_store.search_similarity(
            query_text=query,
            limit=top_k * 2,
            filename_filter=filename_filter
        )

        # Fetch stored chunks to populate BM25 index dynamically
        all_chunks = self.vector_store.get_all_chunks()
        if filename_filter:
            all_chunks = [
                c for c in all_chunks 
                if c.get("metadata", {}).get("filename") == filename_filter
            ]

        self.bm25_service.build_index(all_chunks)
        sparse_results = self.bm25_service.search(query=query, top_k=top_k * 2)

        # Apply Reciprocal Rank Fusion
        return self.reciprocal_rank_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            rrf_k=rrf_k,
            top_k=top_k
        )