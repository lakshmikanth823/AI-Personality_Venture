import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    In-memory sliding window rate limiter for protecting endpoints against DoS and quota abuse.
    Tracks timestamps per client key (IP or user ID).
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.client_records: Dict[str, list] = {}

    def check_rate_limit(self, client_key: str):
        now = time.time()
        window_start = now - self.window_seconds

        if client_key not in self.client_records:
            self.client_records[client_key] = [now]
            return

        # Clean timestamps older than the window
        timestamps = [ts for ts in self.client_records[client_key] if ts > window_start]
        
        if len(timestamps) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Maximum {self.requests_per_minute} requests per minute allowed. Please slow down."
            )

        timestamps.append(now)
        self.client_records[client_key] = timestamps

limiter = SlidingWindowRateLimiter(requests_per_minute=60)

def rate_limit_dependency(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    limiter.check_rate_limit(client_ip)
