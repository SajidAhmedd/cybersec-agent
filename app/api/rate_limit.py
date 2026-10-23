"""
Rate Limiting
Simple in-memory, per-IP limits for endpoints that call the LLM
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

from app.config import settings

_MINUTE = 60
_DAY = 24 * 60 * 60

_requests: dict[str, deque] = defaultdict(deque)
_lock = Lock()


def chat_rate_limit(request: Request):
    """
    FastAPI dependency: reject the request with 429 when the client IP
    exceeds the per-minute or per-day chat limits.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    with _lock:
        timestamps = _requests[client_ip]

        # Drop requests older than a day
        while timestamps and now - timestamps[0] > _DAY:
            timestamps.popleft()

        last_minute = sum(1 for t in timestamps if now - t <= _MINUTE)

        if last_minute >= settings.chat_rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Too many messages. Please wait a minute and try again."
            )
        if len(timestamps) >= settings.chat_rate_limit_per_day:
            raise HTTPException(
                status_code=429,
                detail="Daily message limit reached for this demo. Please try again tomorrow."
            )

        timestamps.append(now)
