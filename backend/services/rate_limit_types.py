"""
Data types for rate limiting service
"""
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class RateLimitInfo:
    """Rate limit information"""
    limit: int
    current: int
    remaining: int
    window_seconds: int
    reset_time: float
    reset_in_seconds: int
    is_limited: bool

    @property
    def reset_time_datetime(self) -> datetime:
        """Get reset time as datetime"""
        return datetime.fromtimestamp(self.reset_time)

    @property
    def usage_percentage(self) -> float:
        """Get usage percentage"""
        if self.limit == 0:
            return 0.0
        return (self.current / self.limit) * 100


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int
    window_seconds: int
    key_prefix: str
    description: Optional[str] = None


@dataclass
class RateLimitCheckResult:
    """Result of rate limit check"""
    allowed: bool
    info: RateLimitInfo
    error_message: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class RateLimitStats:
    """Rate limit statistics"""
    total_keys: int
    active_keys: int
    expired_keys: int
    last_cleanup: float
    next_cleanup_in: int
    storage_type: str = "memory"

    @property
    def last_cleanup_datetime(self) -> datetime:
        """Get last cleanup time as datetime"""
        return datetime.fromtimestamp(self.last_cleanup)


@dataclass
class RateLimitRequestInfo:
    """Rate limit information for a specific request"""
    api_rate_limit: Optional[RateLimitInfo] = None
    sms_rate_limit: Optional[RateLimitInfo] = None
    email_rate_limit: Optional[RateLimitInfo] = None
    client_ip: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "client_ip": self.client_ip,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "rate_limits": {}
        }
        
        if self.api_rate_limit:
            result["rate_limits"]["api"] = {
                "limit": self.api_rate_limit.limit,
                "current": self.api_rate_limit.current,
                "remaining": self.api_rate_limit.remaining,
                "window_seconds": self.api_rate_limit.window_seconds,
                "reset_in_seconds": self.api_rate_limit.reset_in_seconds,
                "is_limited": self.api_rate_limit.is_limited,
                "usage_percentage": self.api_rate_limit.usage_percentage
            }
        
        if self.sms_rate_limit:
            result["rate_limits"]["sms"] = {
                "limit": self.sms_rate_limit.limit,
                "current": self.sms_rate_limit.current,
                "remaining": self.sms_rate_limit.remaining,
                "window_seconds": self.sms_rate_limit.window_seconds,
                "reset_in_seconds": self.sms_rate_limit.reset_in_seconds,
                "is_limited": self.sms_rate_limit.is_limited,
                "usage_percentage": self.sms_rate_limit.usage_percentage
            }
        
        if self.email_rate_limit:
            result["rate_limits"]["email"] = {
                "limit": self.email_rate_limit.limit,
                "current": self.email_rate_limit.current,
                "remaining": self.email_rate_limit.remaining,
                "window_seconds": self.email_rate_limit.window_seconds,
                "reset_in_seconds": self.email_rate_limit.reset_in_seconds,
                "is_limited": self.email_rate_limit.is_limited,
                "usage_percentage": self.email_rate_limit.usage_percentage
            }
        
        return result