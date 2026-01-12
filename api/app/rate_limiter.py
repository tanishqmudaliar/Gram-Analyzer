from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        # Format: {identifier: [(timestamp, count), ...]}
        self.requests: Dict[str, list[Tuple[datetime, int]]] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 60,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if identifier has exceeded rate limit.
        Returns True if allowed, raises HTTPException if rate limited.
        """
        async with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old entries
            self.requests[identifier] = [
                (ts, count) for ts, count in self.requests[identifier]
                if ts > window_start
            ]
            
            # Count requests in current window
            total_requests = sum(count for _, count in self.requests[identifier])
            
            if total_requests >= max_requests:
                retry_after = int((self.requests[identifier][0][0] + timedelta(seconds=window_seconds) - now).total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Add current request
            self.requests[identifier].append((now, 1))
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting."""
    # Use IP or user ID as identifier
    identifier = request.client.host if request.client else "unknown"
    
    # Check if user is authenticated and use their ID
    if hasattr(request.state, "user"):
        identifier = f"user_{request.state.user['id']}"
    
    await rate_limiter.check_rate_limit(
        identifier=identifier,
        max_requests=100,  # 100 requests
        window_seconds=60   # per minute
    )


async def strict_rate_limit_dependency(request: Request):
    """Stricter rate limiting for expensive operations."""
    identifier = request.client.host if request.client else "unknown"
    
    if hasattr(request.state, "user"):
        identifier = f"user_{request.state.user['id']}"
    
    await rate_limiter.check_rate_limit(
        identifier=identifier,
        max_requests=10,    # 10 requests
        window_seconds=60    # per minute
    )