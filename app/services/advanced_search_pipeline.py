from typing import List, Dict, Any, Optional
from app.services.hybrid_search import HybridSearchService
from app.services.reranker_service import RerankerService
from app.services.context_compressor import ContextCompressorService


class AdvancedSearchPipelineService:
    """
    Orchestrator for executing full Advanced RAG Search pipeline:
    Hybrid Search (Dense + Sparse RRF) -> Cross-Encoder Rerank -> Context Compression.
    """

    def __init__(self):
        self.hybrid_service = HybridSearchService()
        self.compressor_service = ContextCompressorService()
        self._reranker_service: Optional[RerankerService] = None

    @property
    def reranker_service(self) -> RerankerService:
        """
        Lazy loader for Cross-Encoder model to avoid overhead at startup.
        """
        if self._reranker_service is None:
            self._reranker_service = RerankerService()
        return self._reranker_service

    def execute_pipeline(
        self,
        query: str,
        top_k: int = 3,
        rrf_k: int = 60,
        min_score_threshold: float = 0.0,
        max_tokens: int = 500,
        enable_rerank: bool = True,
        enable_compression: bool = True,
        filename_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run query through all 3 stages of the Advanced RAG pipeline.
        """
        stages_executed = []

        # Stage 1: Hybrid Search (Retrieve Candidate Candidate Chunks)
        candidate_count = top_k * 3 if (enable_rerank or enable_compression) else top_k
        candidates = self.hybrid_service.search_hybrid(
            query=query,
            top_k=candidate_count,
            rrf_k=rrf_k,
            filename_filter=filename_filter
        )
        stages_executed.append("Stage 1: Hybrid Search (Dense + BM25 Sparse RRF)")

        if not candidates:
            return {
                "pipeline_stages_executed": stages_executed,
                "results": []
            }

        # Stage 2: Cross-Encoder Precision Reranking
        if enable_rerank:
            candidates = self.reranker_service.rerank(
                query=query,
                candidate_chunks=candidates,
                top_k=candidate_count
            )
            stages_executed.append("Stage 2: Cross-Encoder BGE-Reranker Precision Rescoring")

        # Stage 3: Noise Filtering & Context Compression
        if enable_compression:
            final_results = self.compressor_service.process_compression(
                query=query,
                chunks=candidates,
                min_score_threshold=min_score_threshold,
                max_tokens=max_tokens
            )
            stages_executed.append("Stage 3: Context Compression & Noise Threshold Filtering")
        else:
            final_results = candidates[:top_k]

        return {
            "pipeline_stages_executed": stages_executed,
            "results": final_results[:top_k]
        }