"""
Rate limiting service for API endpoints and communications
"""

import time
import threading
import logging
from typing import Optional
from fastapi import Request, HTTPException, status

from common.utils.request_utils import extract_client_ip
from backend.services.rate_limit_types import (
    RateLimitInfo,
    RateLimitConfig,
    RateLimitCheckResult,
    RateLimitStats,
    RateLimitRequestInfo,
)
from backend.utils.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)


class RateLimitService:
    """Service for rate limiting API requests and communications"""

    def __init__(self):
        self.in_memory_storage = {}  # In-memory storage for rate limiting
        self._storage_lock = threading.Lock()  # Thread-safe access
        self._cleanup_interval = 60  # Cleanup every 60 seconds
        self._last_cleanup = time.time()

        # Rate limit configurations
        self.api_rate_limit = RateLimitConfig(
            max_requests=100,
            window_seconds=1,
            key_prefix="api_rate_limit",
            description="API rate limit per IP address",
        )

        self.sms_rate_limit = RateLimitConfig(
            max_requests=1,
            window_seconds=120,  # 2 minutes
            key_prefix="sms_rate_limit",
            description="SMS rate limit per phone number",
        )

        self.email_rate_limit = RateLimitConfig(
            max_requests=2,      # 允许2封邮件
            window_seconds=300,  # 5分钟内
            key_prefix="email_rate_limit",
            description="Email rate limit per email address",
        )

    def _get_storage_key(self, prefix: str, identifier: str) -> str:
        """Generate storage key for rate limiting"""
        return f"{prefix}:{identifier}"

    def _get_current_timestamp(self) -> float:
        """Get current timestamp"""
        return time.time()

    def _set_in_memory_value(self, key: str, value: dict, expire_seconds: int):
        """Set value in in-memory storage"""
        with self._storage_lock:
            self.in_memory_storage[key] = {
                "value": value,
                "expire_at": self._get_current_timestamp() + expire_seconds,
            }
        # Trigger periodic cleanup if needed
        self._trigger_cleanup_if_needed()

    def _get_in_memory_value(self, key: str) -> Optional[dict]:
        """Get value from in-memory storage"""
        with self._storage_lock:
            if key in self.in_memory_storage:
                entry = self.in_memory_storage[key]
                if entry["expire_at"] > self._get_current_timestamp():
                    return entry["value"]
                else:
                    del self.in_memory_storage[key]
        return None

    def _trigger_cleanup_if_needed(self):
        """Trigger cleanup if enough time has passed"""
        current_time = self._get_current_timestamp()
        if current_time - self._last_cleanup >= self._cleanup_interval:
            self._cleanup_in_memory_storage()
            self._last_cleanup = current_time

    def _cleanup_in_memory_storage(self):
        """Clean up expired in-memory entries"""
        current_time = self._get_current_timestamp()
        with self._storage_lock:
            expired_keys = [
                key
                for key, entry in self.in_memory_storage.items()
                if entry["expire_at"] <= current_time
            ]
            for key in expired_keys:
                del self.in_memory_storage[key]

            if expired_keys:
                logger.info(
                    f"Cleaned up {len(expired_keys)} expired rate limit entries"
                )

    def get_storage_stats(self) -> RateLimitStats:
        """Get storage statistics for monitoring"""
        with self._storage_lock:
            current_time = self._get_current_timestamp()
            total_keys = len(self.in_memory_storage)
            expired_keys = sum(
                1
                for entry in self.in_memory_storage.values()
                if entry["expire_at"] <= current_time
            )

            return RateLimitStats(
                total_keys=total_keys,
                active_keys=total_keys - expired_keys,
                expired_keys=expired_keys,
                last_cleanup=self._last_cleanup,
                next_cleanup_in=max(
                    0, self._cleanup_interval - (current_time - self._last_cleanup)
                ),
            )

    def _check_rate_limit_internal(
        self, config: RateLimitConfig, identifier: str
    ) -> RateLimitCheckResult:
        """Internal rate limit checking logic"""
        key = self._get_storage_key(config.key_prefix, identifier)
        current_time = self._get_current_timestamp()
        window_start = current_time - config.window_seconds

        # Get from in-memory storage
        request_data = self._get_in_memory_value(key)

        if request_data is None:
            # First request in window - don't include current request yet
            request_data = {"requests": [], "window_start": window_start}
        else:
            # Clean up old requests
            request_data["requests"] = [
                req_time
                for req_time in request_data["requests"]
                if req_time > window_start
            ]
            request_data["window_start"] = window_start

        # Create rate limit info
        reset_time = request_data["window_start"] + config.window_seconds
        reset_in_seconds = int(reset_time - current_time)
        current_requests = len(request_data["requests"])

        # Debug logging for email rate limits
        if config.key_prefix == "email_rate_limit":
            logger.info(f"Email rate limit check: identifier={identifier}, current_requests={current_requests}, limit={config.max_requests}, window={config.window_seconds}s")

        rate_info = RateLimitInfo(
            limit=config.max_requests,
            current=current_requests,
            remaining=max(0, config.max_requests - current_requests),
            window_seconds=config.window_seconds,
            reset_time=reset_time,
            reset_in_seconds=reset_in_seconds,
            is_limited=current_requests >= config.max_requests,
        )

        # Check if rate limit exceeded
        if rate_info.is_limited:
            logger.warning(f"Rate limit exceeded for {identifier}: {current_requests}/{config.max_requests} requests in {config.window_seconds}s window")
            return RateLimitCheckResult(
                allowed=False,
                info=rate_info,
                error_message=f"Rate limit exceeded: {config.max_requests} requests per {config.window_seconds}s",
                error_type="rate_limit_exceeded",
            )

        # Add current request
        request_data["requests"].append(current_time)

        # Store back
        expire_seconds = int(config.window_seconds)
        self._set_in_memory_value(key, request_data, expire_seconds)

        # Update info with the new request
        rate_info.current += 1
        rate_info.remaining = max(0, config.max_requests - rate_info.current)
        rate_info.is_limited = False

        return RateLimitCheckResult(allowed=True, info=rate_info)

    @circuit_breaker("api_rate_limit_check", failure_threshold=3, recovery_timeout=30)
    def check_api_rate_limit(self, request: Request) -> bool:
        """Check API rate limit for IP address"""
        try:
            client_ip = extract_client_ip(request)
        except Exception as e:
            logger.warning(f"Failed to extract client IP: {e}")
            # If IP extraction fails, allow the request but log it
            return True

        result = self._check_rate_limit_internal(self.api_rate_limit, client_ip)

        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": result.error_message,
                    "type": "api_rate_limit",
                    "limit": result.info.limit,
                    "window": f"{self.api_rate_limit.window_seconds}s",
                    "reset_in": result.info.reset_in_seconds,
                    "usage_percentage": result.info.usage_percentage,
                },
            )

        return True

    @circuit_breaker("sms_rate_limit_check", failure_threshold=3, recovery_timeout=30)
    def check_sms_rate_limit(self, phone_number: str) -> bool:
        """Check SMS rate limit for phone number"""
        result = self._check_rate_limit_internal(self.sms_rate_limit, phone_number)

        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": result.error_message,
                    "type": "sms_rate_limit",
                    "limit": result.info.limit,
                    "window": f"{self.sms_rate_limit.window_seconds}s",
                    "reset_in": result.info.reset_in_seconds,
                    "phone": phone_number[-4:],  # Show last 4 digits only
                    "usage_percentage": result.info.usage_percentage,
                },
            )

        return True

    @circuit_breaker("email_rate_limit_check", failure_threshold=3, recovery_timeout=30)
    def check_email_rate_limit(self, email: str) -> bool:
        """Check email rate limit for email address"""
        result = self._check_rate_limit_internal(self.email_rate_limit, email)

        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": result.error_message,
                    "type": "email_rate_limit",
                    "limit": result.info.limit,
                    "window": f"{self.email_rate_limit.window_seconds}s",
                    "reset_in": result.info.reset_in_seconds,
                    "email": email,
                    "usage_percentage": result.info.usage_percentage,
                },
            )

        return True

    def get_rate_limit_info(self, request: Request) -> RateLimitRequestInfo:
        """Get current rate limit info for debugging"""
        try:
            client_ip = extract_client_ip(request)
        except Exception as e:
            logger.warning(f"Failed to extract client IP for rate limit info: {e}")
            return RateLimitRequestInfo(client_ip="unknown")

        request_info = RateLimitRequestInfo(client_ip=client_ip)

        # Check each rate limit type
        for config in [self.api_rate_limit, self.sms_rate_limit, self.email_rate_limit]:
            key = self._get_storage_key(config.key_prefix, client_ip)
            request_data = self._get_in_memory_value(key)

            if request_data:
                current_time = self._get_current_timestamp()
                window_start = current_time - config.window_seconds
                active_requests = [
                    req_time
                    for req_time in request_data["requests"]
                    if req_time > window_start
                ]

                reset_time = request_data["window_start"] + config.window_seconds
                rate_info = RateLimitInfo(
                    limit=config.max_requests,
                    current=len(active_requests),
                    remaining=max(0, config.max_requests - len(active_requests)),
                    window_seconds=config.window_seconds,
                    reset_time=reset_time,
                    reset_in_seconds=int(reset_time - current_time),
                    is_limited=len(active_requests) >= config.max_requests,
                )

                # Set the appropriate field based on config type
                if config.key_prefix == "api_rate_limit":
                    request_info.api_rate_limit = rate_info
                elif config.key_prefix == "sms_rate_limit":
                    request_info.sms_rate_limit = rate_info
                elif config.key_prefix == "email_rate_limit":
                    request_info.email_rate_limit = rate_info

        return request_info


# Global service instance
_rate_limit_service = None


def get_rate_limit_service() -> RateLimitService:
    """Get rate limit service instance"""
    global _rate_limit_service
    if _rate_limit_service is None:
        _rate_limit_service = RateLimitService()
    return _rate_limit_service
