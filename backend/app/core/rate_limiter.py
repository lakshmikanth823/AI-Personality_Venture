import time
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class SlidingWindowRateLimiter:
    """
    In-memory sliding window rate limiter for protecting endpoints against DoS and abuse.
    Tracks timestamps per client key (IP or user ID).
    """
    def __init__(self, default_limit: int = 120, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.client_records: Dict[str, List[float]] = {}
        # Route-specific limit overrides (e.g. login brute-force prevention)
        self.route_limits: Dict[str, int] = {
            "/api/v1/auth/login": 15,
            "/api/v1/auth/signup": 10
        }

    def get_limit_for_path(self, path: str) -> int:
        for prefix, lim in self.route_limits.items():
            if path.startswith(prefix):
                return lim
        return self.default_limit

    def is_allowed(self, client_key: str, limit: Optional[int] = None) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        max_reqs = limit if limit is not None else self.default_limit

        if client_key not in self.client_records:
            self.client_records[client_key] = [now]
            return True

        # Purge expired timestamps
        timestamps = [ts for ts in self.client_records[client_key] if ts > window_start]

        if len(timestamps) >= max_reqs:
            self.client_records[client_key] = timestamps
            return False

        timestamps.append(now)
        self.client_records[client_key] = timestamps
        return True

    def check_rate_limit(self, client_key: str, limit: Optional[int] = None):
        if not self.is_allowed(client_key, limit):
            max_reqs = limit if limit is not None else self.default_limit
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Maximum {max_reqs} requests per minute allowed. Please slow down."
            )

    def reset(self):
        self.client_records.clear()

limiter = SlidingWindowRateLimiter(default_limit=120)

def get_client_ip(request: Request, behind_trusted_proxy: bool = False) -> str:
    """
    Extracts client IP with spoofing defense.
    Only honours X-Forwarded-For if explicitly configured behind a trusted reverse proxy.
    Otherwise defaults to direct socket client host to prevent header spoofing.
    """
    if behind_trusted_proxy:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # First non-empty trimmed IP from chain
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                return parts[0]
    return request.client.host if request.client else "127.0.0.1"

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, behind_trusted_proxy: bool = False):
        super().__init__(app)
        self.behind_trusted_proxy = behind_trusted_proxy

    async def dispatch(self, request: Request, call_next):
        # Exclude static assets and health check
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        client_ip = get_client_ip(request, behind_trusted_proxy=self.behind_trusted_proxy)
        from backend.app.core.config import settings
        if client_ip == "testclient" and getattr(settings, "ENVIRONMENT", "") == "test":
            req_limit = 10000
        else:
            req_limit = limiter.get_limit_for_path(path)

        if not limiter.is_allowed(client_ip, limit=req_limit):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded: Maximum {req_limit} requests per minute allowed on this endpoint. Please slow down."
                }
            )

        response = await call_next(request)
        return response

def rate_limit_dependency(request: Request):
    client_ip = get_client_ip(request, behind_trusted_proxy=False)
    limiter.check_rate_limit(client_ip)
