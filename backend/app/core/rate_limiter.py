import time
import uuid
import logging
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Attempt Redis connection for distributed rate limiting
_redis_client = None
try:
    import redis
    if settings.REDIS_URL and getattr(settings, "APP_ENV", "") != "test":
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.0)
        # Quick ping to verify connectivity
        _redis_client.ping()
except Exception as e:
    logger.info(f"Redis rate limiter unavailable ({e}), using in-memory sliding window rate limiter.")
    _redis_client = None

class SlidingWindowRateLimiter:
    """
    Distributed (Redis-backed) and in-memory sliding window rate limiter
    for protecting endpoints against DoS, brute-force, and abuse.
    """
    def __init__(self, default_limit: int = 120, window_seconds: int = 60, redis_url: Optional[str] = None):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.client_records: Dict[str, List[float]] = {}
        self.redis_client = None
        
        # Connect to redis if provided and reachable
        if redis_url and getattr(settings, "APP_ENV", "") != "test":
            try:
                import redis
                r = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1.0)
                r.ping()
                self.redis_client = r
            except Exception:
                self.redis_client = None
        elif _redis_client is not None:
            self.redis_client = _redis_client

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

        # 1. Distributed Redis sliding window
        if self.redis_client:
            try:
                key = f"ratelimit:{client_key}"
                pipe = self.redis_client.pipeline()
                # Remove timestamps older than current window
                pipe.zremrangebyscore(key, 0, window_start)
                # Count requests in window
                pipe.zcard(key)
                # Add current request timestamp
                pipe.zadd(key, {f"{now}:{uuid.uuid4().hex[:6]}": now})
                # Set TTL to window + 5s buffer
                pipe.expire(key, self.window_seconds + 5)
                results = pipe.execute()
                
                req_count = results[1] # count before adding current
                if req_count >= max_reqs:
                    return False
                return True
            except Exception as ex:
                logger.warning(f"Redis rate limit check failed ({ex}), falling back to in-memory.")

        # 2. In-Memory fallback
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
        if self.redis_client:
            try:
                keys = self.redis_client.keys("ratelimit:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception:
                pass

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
        if getattr(settings, "APP_ENV", "") == "test" or getattr(settings, "ENVIRONMENT", "") == "test":
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

        return await call_next(request)
