"""
Structured Logging, Request ID, and Rate Limiting Middleware.
"""
import time
import uuid
import logging
from typing import Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.config import settings

# Setup structured logger
logger = logging.getLogger("querylens")
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
)

# In-memory sliding rate limiter per client IP
# { ip: [timestamp_1, timestamp_2, ...] }
RATE_LIMIT_BUCKETS: Dict[str, List[float]] = {}


class ObservabilityAndRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Assign or propagate Request ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = req_id

        # 2. Rate limiting check (e.g. 60 requests/minute per client IP)
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean timestamps older than 60s
        history = RATE_LIMIT_BUCKETS.get(client_ip, [])
        history = [t for t in history if now - t < 60.0]
        
        if len(history) >= settings.api_rate_limit_per_minute and not request.url.path.startswith("/api/health"):
            RATE_LIMIT_BUCKETS[client_ip] = history
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path} [req_id={req_id}]")
            return Response(
                content='{"detail": "API rate limit exceeded. Please try again in 1 minute."}',
                status_code=429,
                media_type="application/json",
                headers={"X-Request-ID": req_id, "Retry-After": "60"}
            )
            
        history.append(now)
        RATE_LIMIT_BUCKETS[client_ip] = history

        # 3. Optional Simple Bearer Auth (if API_SECRET_KEY is configured)
        if settings.api_secret_key:
            auth_header = request.headers.get("Authorization", "")
            expected_auth = f"Bearer {settings.api_secret_key}"
            if request.url.path.startswith("/api") and not request.url.path.startswith("/api/health"):
                if auth_header != expected_auth:
                    return Response(
                        content='{"detail": "Unauthorized: Invalid or missing API bearer token."}',
                        status_code=401,
                        media_type="application/json",
                        headers={"X-Request-ID": req_id}
                    )

        # 4. Measure request duration
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = req_id
            logger.info(f"{request.method} {request.url.path} {response.status_code} in {duration_ms}ms [req_id={req_id}]")
            return response
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"Unhandled exception on {request.method} {request.url.path} in {duration_ms}ms [req_id={req_id}]: {str(e)}")
            return Response(
                content='{"detail": "Internal server error occurred. Please contact system administrator."}',
                status_code=500,
                media_type="application/json",
                headers={"X-Request-ID": req_id}
            )
