from pydantic import BaseModel, Field
from typing import List, Optional


class EvalTestCase(BaseModel):
    """
    Single ground-truth evaluation query and expected relevance keywords.
    """
    query: str = Field(..., description="Evaluation search query")
    expected_keywords: List[str] = Field(
        ..., description="Case-insensitive terms expected in relevant retrieved chunks"
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Number of chunks to retrieve")
    min_score_threshold: float = Field(
        default=-5.0, description="Cross-encoder relevance score cutoff"
    )


class EvalRequest(BaseModel):
    """
    Request payload for running a RAG retrieval and faithfulness benchmark.
    """
    test_cases: Optional[List[EvalTestCase]] = Field(
        default=None,
        description="Custom evaluation cases; defaults to built-in platform golden dataset if omitted",
    )
    compare_baseline: bool = Field(
        default=True,
        description="Compare Stage-1 Hybrid baseline against Full Reranked + Compressed pipeline",
    )


class CaseEvalResult(BaseModel):
    """
    Per-query retrieval and synthesis quality metrics.
    """
    query: str
    precision_at_k: float
    reciprocal_rank: float
    faithfulness_score: float
    retrieved_count: int
    matched_keywords: List[str]
    synthesis_mode: str
    latency_ms: float


class BaselineComparison(BaseModel):
    """
    Metric delta between Stage-1 Hybrid retrieval and Full Advanced RAG pipeline.
    """
    baseline_precision_at_k: float
    advanced_precision_at_k: float
    precision_delta: float
    baseline_mrr: float
    advanced_mrr: float
    mrr_delta: float


class EvalSummaryResponse(BaseModel):
    """
    Aggregated benchmark report across all evaluation queries.
    """
    status: str
    total_cases: int
    mean_precision_at_k: float
    mrr: float
    mean_faithfulness: float
    avg_latency_ms: float
    baseline_comparison: Optional[BaselineComparison] = None
    case_results: List[CaseEvalResult]