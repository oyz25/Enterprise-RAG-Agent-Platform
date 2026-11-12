from fastapi import APIRouter, HTTPException, status
from app.schemas.evaluation import EvalRequest, EvalSummaryResponse
from app.services.evaluation_service import RAGEvaluationService

router = APIRouter(prefix="/api/v1/evaluate", tags=["RAG Evaluation Benchmark"])
eval_service = RAGEvaluationService()


@router.post("/run", response_model=EvalSummaryResponse)
def run_rag_evaluation(request: EvalRequest = EvalRequest()):
    """
    Execute automated RAG benchmark measuring Precision@K, MRR, and Answer Faithfulness.
    """
    try:
        return eval_service.run_benchmark(
            test_cases=request.test_cases,
            compare_baseline=request.compare_baseline,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG evaluation benchmark failed: {str(e)}",
        )