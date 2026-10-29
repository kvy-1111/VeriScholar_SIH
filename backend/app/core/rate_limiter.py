from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.buckets: dict[str, deque[datetime]] = defaultdict(deque)

    def check(self, key: str):
        now = datetime.utcnow()
        threshold = now - timedelta(seconds=self.window_seconds)
        bucket = self.buckets[key]
        while bucket and bucket[0] < threshold:
            bucket.popleft()
        if len(bucket) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests")
        bucket.append(now)


login_limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
public_verify_limiter = InMemoryRateLimiter(limit=30, window_seconds=60)


def rate_limit_login(request: Request):
    login_limiter.check(request.client.host if request.client else "unknown")


def rate_limit_public_verify(request: Request):
    public_verify_limiter.check(request.client.host if request.client else "unknown")
