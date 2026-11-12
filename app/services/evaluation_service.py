import re
import time
from typing import List, Dict, Any, Tuple
from app.schemas.agent import AgentIntent
from app.schemas.evaluation import (
    EvalTestCase,
    CaseEvalResult,
    BaselineComparison,
    EvalSummaryResponse,
)
from app.services.advanced_search_pipeline import AdvancedSearchPipelineService
from app.services.llm_synthesizer import LLMSynthesizerService

STOPWORDS = {
    "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for",
    "of", "with", "as", "by", "that", "this", "it", "from", "or", "be", "are",
    "was", "were", "has", "have", "had", "based", "retrieved", "context", "here",
    "answer", "grounded", "source", "sources", "references", "chunk", "relevance",
}

DEFAULT_GOLDEN_CASES: List[EvalTestCase] = [
    EvalTestCase(
        query="FastAPI REST API backend experience",
        expected_keywords=["fastapi", "rest", "python", "api"],
        top_k=3,
        min_score_threshold=-5.0,
    ),
    EvalTestCase(
        query="SQLAlchemy relational database architecture",
        expected_keywords=["sqlalchemy", "database", "sql", "pydantic"],
        top_k=3,
        min_score_threshold=-5.0,
    ),
    EvalTestCase(
        query="Student Financial Management System project",
        expected_keywords=["financial", "student", "system", "management"],
        top_k=3,
        min_score_threshold=-5.0,
    ),
    EvalTestCase(
        query="Software engineering internship availability",
        expected_keywords=["internship", "software", "engineering", "student"],
        top_k=3,
        min_score_threshold=-5.0,
    ),
]


class RAGEvaluationService:
    """
    Evaluates retrieval ranking quality (Precision@K, MRR) and answer groundedness (Faithfulness).
    """

    def __init__(self):
        self.pipeline = AdvancedSearchPipelineService()
        self.synthesizer = LLMSynthesizerService()

    @staticmethod
    def _tokenize_content(text: str) -> set[str]:
        tokens = set(re.findall(r"[a-z0-9]{2,}", text.lower()))
        return tokens - STOPWORDS

    @staticmethod
    def _score_retrieval(
        chunks: List[Dict[str, Any]], expected_keywords: List[str]
    ) -> Tuple[float, float, List[str]]:
        """
        Compute Precision@K and Reciprocal Rank for a ranked list of retrieved chunks.
        """
        if not chunks:
            return 0.0, 0.0, []

        normalized_keywords = [kw.lower().strip() for kw in expected_keywords if kw.strip()]
        relevant_hits = 0
        first_relevant_rank = 0
        matched_kw_set: set[str] = set()

        for rank_idx, chunk in enumerate(chunks, start=1):
            text = (chunk.get("compressed_text") or chunk.get("text", "")).lower()
            chunk_matches = [kw for kw in normalized_keywords if kw in text]
            if chunk_matches:
                relevant_hits += 1
                matched_kw_set.update(chunk_matches)
                if first_relevant_rank == 0:
                    first_relevant_rank = rank_idx

        precision_at_k = round(relevant_hits / len(chunks), 4)
        reciprocal_rank = round(1.0 / first_relevant_rank, 4) if first_relevant_rank > 0 else 0.0
        return precision_at_k, reciprocal_rank, sorted(matched_kw_set)

    def _score_faithfulness(self, answer: str, chunks: List[Dict[str, Any]]) -> float:
        """
        Measure proportion of substantive answer tokens grounded in retrieved source chunks.
        """
        # Strip appended References footer before checking claim groundedness
        body = answer.split("**References:**")[0].strip()
        answer_tokens = self._tokenize_content(body)

        if not chunks:
            # Unanswered fallback without hallucinated claims is considered faithful
            return 1.0 if "no matching" in body.lower() else 0.0

        if not answer_tokens:
            return 1.0

        context_text = " ".join(
            (c.get("compressed_text") or c.get("text", "")) for c in chunks
        )
        context_tokens = self._tokenize_content(context_text)
        if not context_tokens:
            return 0.0

        grounded_tokens = answer_tokens.intersection(context_tokens)
        return round(len(grounded_tokens) / len(answer_tokens), 4)

    def run_benchmark(
        self,
        test_cases: List[EvalTestCase] | None = None,
        compare_baseline: bool = True,
    ) -> EvalSummaryResponse:
        cases = test_cases if test_cases else DEFAULT_GOLDEN_CASES

        case_results: List[CaseEvalResult] = []
        baseline_precisions: List[float] = []
        baseline_rrs: List[float] = []

        for case in cases:
            # Optional Stage-1 Hybrid-only baseline run (no rerank, no compression)
            if compare_baseline:
                base_out = self.pipeline.execute_pipeline(
                    query=case.query,
                    top_k=case.top_k,
                    enable_rerank=False,
                    enable_compression=False,
                )
                b_prec, b_rr, _ = self._score_retrieval(
                    base_out["results"], case.expected_keywords
                )
                baseline_precisions.append(b_prec)
                baseline_rrs.append(b_rr)

            # Full Advanced Pipeline + Grounded Synthesis run
            start_time = time.perf_counter()
            adv_out = self.pipeline.execute_pipeline(
                query=case.query,
                top_k=case.top_k,
                min_score_threshold=case.min_score_threshold,
                enable_rerank=True,
                enable_compression=True,
            )
            chunks = adv_out["results"]

            synthesis = self.synthesizer.synthesize(
                query=case.query,
                intent=AgentIntent.KNOWLEDGE_BASE,
                result_data=adv_out,
                history=[],
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            prec, rr, matched_kws = self._score_retrieval(chunks, case.expected_keywords)
            faithfulness = self._score_faithfulness(synthesis["answer"], chunks)

            case_results.append(
                CaseEvalResult(
                    query=case.query,
                    precision_at_k=prec,
                    reciprocal_rank=rr,
                    faithfulness_score=faithfulness,
                    retrieved_count=len(chunks),
                    matched_keywords=matched_kws,
                    synthesis_mode=synthesis["synthesis_mode"],
                    latency_ms=elapsed_ms,
                )
            )

        total = len(case_results)
        mean_prec = round(sum(r.precision_at_k for r in case_results) / total, 4)
        mrr = round(sum(r.reciprocal_rank for r in case_results) / total, 4)
        mean_faith = round(sum(r.faithfulness_score for r in case_results) / total, 4)
        avg_lat = round(sum(r.latency_ms for r in case_results) / total, 2)

        comparison = None
        if compare_baseline and baseline_precisions:
            base_mean_prec = round(sum(baseline_precisions) / total, 4)
            base_mrr = round(sum(baseline_rrs) / total, 4)
            comparison = BaselineComparison(
                baseline_precision_at_k=base_mean_prec,
                advanced_precision_at_k=mean_prec,
                precision_delta=round(mean_prec - base_mean_prec, 4),
                baseline_mrr=base_mrr,
                advanced_mrr=mrr,
                mrr_delta=round(mrr - base_mrr, 4),
            )

        return EvalSummaryResponse(
            status="success",
            total_cases=total,
            mean_precision_at_k=mean_prec,
            mrr=mrr,
            mean_faithfulness=mean_faith,
            avg_latency_ms=avg_lat,
            baseline_comparison=comparison,
            case_results=case_results,
        )