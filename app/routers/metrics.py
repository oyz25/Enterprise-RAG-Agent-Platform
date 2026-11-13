from fastapi import APIRouter
from app.core.telemetry import telemetry_store
from app.schemas.metrics import MetricsResponse, MetricsResetResponse

router = APIRouter(prefix="/api/v1/metrics", tags=["Telemetry & Observability"])


@router.get("", response_model=MetricsResponse)
def get_platform_metrics():
    """
    Return real-time request throughput, error rates, and per-endpoint latency percentiles.
    """
    stats = telemetry_store.snapshot()
    return MetricsResponse(
        status="success",
        service="RAG-Agent-Engine",
        version="1.0.0",
        **stats,
    )


@router.post("/reset", response_model=MetricsResetResponse)
def reset_platform_metrics():
    """
    Reset in-memory telemetry counters for clean benchmark runs.
    """
    telemetry_store.reset()
    return MetricsResetResponse(
        status="success",
        message="Telemetry metrics counters have been reset.",
    )