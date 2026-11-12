from pydantic import BaseModel
from typing import Dict, List


class EndpointMetricItem(BaseModel):
    endpoint: str
    requests: int
    errors: int
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float


class MetricsResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: float
    total_requests: int
    total_errors: int
    error_rate_percent: float
    avg_latency_ms: float
    status_code_counts: Dict[str, int]
    endpoints: List[EndpointMetricItem]


class MetricsResetResponse(BaseModel):
    status: str
    message: str