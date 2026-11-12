import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.telemetry import app_logger, request_id_ctx, telemetry_store


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Intercepts every HTTP request to assign a correlation ID, measure high-resolution
    latency, emit structured JSON access logs, and update telemetry metrics.
    """

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(correlation_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            telemetry_store.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            response.headers["X-Request-ID"] = correlation_id
            response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"

            app_logger.info(
                "http.request.completed",
                extra={
                    "structured": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    }
                },
            )
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            telemetry_store.record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
            )
            app_logger.error(
                "http.request.failed",
                exc_info=True,
                extra={
                    "structured": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": 500,
                        "duration_ms": duration_ms,
                        "error": str(exc),
                    }
                },
            )
            raise
        finally:
            request_id_ctx.reset(token)