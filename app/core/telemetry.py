import json
import logging
import sys
import threading
import time
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List

# ContextVar propagates the active request correlation ID across async call stacks
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="system")


class StructuredJsonFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects for log aggregators (ELK, Datadog, CloudWatch).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_ctx.get(),
            "message": record.getMessage(),
        }

        # Attach structured metadata passed via logger.info(..., extra={"structured": {...}})
        structured_extra = getattr(record, "structured", None)
        if isinstance(structured_extra, dict):
            log_payload.update(structured_extra)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, default=str)


def configure_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure application logger to emit structured JSON lines to stdout.
    """
    logger = logging.getLogger("enterprise_rag")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


class TelemetryStore:
    """
    Thread-safe in-memory metrics collector tracking request counts, error rates,
    status codes, and bounded sliding-window latency distributions per endpoint.
    """

    def __init__(self, window_size: int = 500):
        self._lock = threading.Lock()
        self._window_size = window_size
        self._start_time = time.time()
        self._total_requests = 0
        self._total_errors = 0
        self._status_counts: Dict[str, int] = {}
        self._routes: Dict[str, Dict[str, Any]] = {}

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        route_key = f"{method} {path}"
        status_str = str(status_code)
        is_error = status_code >= 400

        with self._lock:
            self._total_requests += 1
            if is_error:
                self._total_errors += 1

            self._status_counts[status_str] = self._status_counts.get(status_str, 0) + 1

            if route_key not in self._routes:
                self._routes[route_key] = {
                    "method": method,
                    "path": path,
                    "count": 0,
                    "error_count": 0,
                    "total_duration_ms": 0.0,
                    "min_duration_ms": duration_ms,
                    "max_duration_ms": duration_ms,
                    "recent_durations": deque(maxlen=self._window_size),
                }

            stats = self._routes[route_key]
            stats["count"] += 1
            if is_error:
                stats["error_count"] += 1
            stats["total_duration_ms"] += duration_ms
            stats["min_duration_ms"] = min(stats["min_duration_ms"], duration_ms)
            stats["max_duration_ms"] = max(stats["max_duration_ms"], duration_ms)
            stats["recent_durations"].append(duration_ms)

    @staticmethod
    def _compute_p95(durations: Deque[float]) -> float:
        if not durations:
            return 0.0
        sorted_vals = sorted(durations)
        idx = min(int(len(sorted_vals) * 0.95), len(sorted_vals) - 1)
        return round(sorted_vals[idx], 2)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            uptime = round(time.time() - self._start_time, 2)
            total_req = self._total_requests
            total_err = self._total_errors
            error_rate = round((total_err / total_req) * 100, 2) if total_req > 0 else 0.0

            endpoints: List[Dict[str, Any]] = []
            overall_duration_sum = 0.0

            for route_key, stats in sorted(self._routes.items()):
                count = stats["count"]
                total_dur = stats["total_duration_ms"]
                overall_duration_sum += total_dur
                avg_dur = round(total_dur / count, 2) if count > 0 else 0.0

                endpoints.append({
                    "endpoint": route_key,
                    "requests": count,
                    "errors": stats["error_count"],
                    "avg_latency_ms": avg_dur,
                    "min_latency_ms": round(stats["min_duration_ms"], 2),
                    "max_latency_ms": round(stats["max_duration_ms"], 2),
                    "p95_latency_ms": self._compute_p95(stats["recent_durations"]),
                })

            overall_avg = round(overall_duration_sum / total_req, 2) if total_req > 0 else 0.0

            return {
                "uptime_seconds": uptime,
                "total_requests": total_req,
                "total_errors": total_err,
                "error_rate_percent": error_rate,
                "avg_latency_ms": overall_avg,
                "status_code_counts": dict(self._status_counts),
                "endpoints": endpoints,
            }

    def reset(self) -> None:
        with self._lock:
            self._start_time = time.time()
            self._total_requests = 0
            self._total_errors = 0
            self._status_counts.clear()
            self._routes.clear()


# Singleton logger and telemetry store
app_logger = configure_structured_logging()
telemetry_store = TelemetryStore()