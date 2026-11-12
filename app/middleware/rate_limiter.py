import os
import threading
import time
from collections import deque
from typing import Deque, Dict, Tuple
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.telemetry import app_logger

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class SlidingWindowRateLimiter:
    """
    Thread-safe per-client-IP sliding window rate limiter backed by monotonic timestamps.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self._lock = threading.Lock()
        self.max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", str(max_requests)))
        self.window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", str(window_seconds)))
        self._buckets: Dict[str, Deque[float]] = {}

    def check(self, client_key: str) -> Tuple[bool, int, int]:
        """
        Evaluate whether client_key is within rate quota.
        Returns (allowed, remaining_requests, retry_after_seconds).
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            bucket = self._buckets.setdefault(client_key, deque())

            # Evict timestamps outside the sliding window
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                oldest = bucket[0]
                retry_after = max(1, int((oldest + self.window_seconds) - now) + 1)
                return False, 0, retry_after

            bucket.append(now)
            remaining = max(0, self.max_requests - len(bucket))
            return True, remaining, 0

    def reset(self) -> None:
        """
        Clear all client rate-limit buckets.
        """
        with self._lock:
            self._buckets.clear()


rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces per-IP sliding window rate limits and attaches X-RateLimit-* headers.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        allowed, remaining, retry_after = rate_limiter.check(client_ip)

        if not allowed:
            app_logger.warning(
                "security.rate_limit.exceeded",
                extra={
                    "structured": {
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "retry_after": retry_after,
                    }
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "detail": f"Rate limit exceeded. Retry after {retry_after} seconds.",
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response