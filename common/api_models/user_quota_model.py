from pydantic import BaseModel, ConfigDict, Field, validator
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class QuotaType(str, Enum):
    """Quota type enumeration"""
    CREDITS = "credits"
    TOKENS = "tokens"


class OperationType(str, Enum):
    """Quota operation type enumeration"""
    CONSUME = "consume"
    REFUND = "refund"
    RESET = "reset"
    UPGRADE = "upgrade"


class QuotaCurrentResponse(BaseModel):
    """Current quota status response"""
    user_id: str
    quota_type: str
    daily_limit: float
    used_amount: float
    remaining_amount: float
    usage_percentage: float
    reset_date: date
    is_active: bool
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotaUsageLogResponse(BaseModel):
    """Quota usage log response"""
    id: int
    user_id: str
    quota_type: str
    amount: float
    operation_type: str
    related_request_uuid: Optional[str] = None
    quota_before: Optional[float] = None
    quota_after: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotaUsageHistoryResponse(BaseModel):
    """Quota usage history response with pagination"""
    usage_logs: List[QuotaUsageLogResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class QuotaCheckRequest(BaseModel):
    """Request to check if quota is sufficient"""
    quota_type: str = Field(default="credits", description="Type of quota to check")
    amount: float = Field(gt=0, description="Amount to check")

    @validator('quota_type')
    def validate_quota_type(cls, v):
        if v not in [qt.value for qt in QuotaType]:
            raise ValueError(f"Invalid quota type. Must be one of: {[qt.value for qt in QuotaType]}")
        return v


class QuotaCheckResponse(BaseModel):
    """Response for quota check"""
    is_sufficient: bool
    current_quota: QuotaCurrentResponse
    requested_amount: float


class QuotaConsumeRequest(BaseModel):
    """Request to consume quota"""
    quota_type: str = Field(default="credits", description="Type of quota to consume")
    amount: float = Field(gt=0, description="Amount to consume")
    related_request_uuid: Optional[str] = Field(None, description="Related request UUID")
    description: Optional[str] = Field(None, description="Operation description")

    @validator('quota_type')
    def validate_quota_type(cls, v):
        if v not in [qt.value for qt in QuotaType]:
            raise ValueError(f"Invalid quota type. Must be one of: {[qt.value for qt in QuotaType]}")
        return v


class QuotaRefundRequest(BaseModel):
    """Request to refund quota"""
    quota_type: str = Field(default="credits", description="Type of quota to refund")
    amount: float = Field(gt=0, description="Amount to refund")
    related_request_uuid: Optional[str] = Field(None, description="Related request UUID")
    description: Optional[str] = Field(None, description="Refund reason")

    @validator('quota_type')
    def validate_quota_type(cls, v):
        if v not in [qt.value for qt in QuotaType]:
            raise ValueError(f"Invalid quota type. Must be one of: {[qt.value for qt in QuotaType]}")
        return v


class QuotaOperationResponse(BaseModel):
    """Response for quota operations (consume/refund)"""
    success: bool
    operation_type: str
    amount: float
    quota_before: float
    quota_after: float
    remaining_amount: float
    log_id: int
    timestamp: datetime


# Admin API Models

class AdminQuotaAdjustRequest(BaseModel):
    """Admin request to adjust user quota"""
    user_id: str = Field(description="User ID to adjust quota for")
    quota_type: str = Field(default="credits", description="Type of quota")
    new_daily_limit: float = Field(ge=0, description="New daily quota limit")
    reason: Optional[str] = Field(None, description="Reason for adjustment")

    @validator('quota_type')
    def validate_quota_type(cls, v):
        if v not in [qt.value for qt in QuotaType]:
            raise ValueError(f"Invalid quota type. Must be one of: {[qt.value for qt in QuotaType]}")
        return v


class AdminQuotaResetRequest(BaseModel):
    """Admin request to reset user quota"""
    user_id: str = Field(description="User ID to reset quota for")
    quota_type: str = Field(default="credits", description="Type of quota")
    reason: Optional[str] = Field(None, description="Reason for reset")

    @validator('quota_type')
    def validate_quota_type(cls, v):
        if v not in [qt.value for qt in QuotaType]:
            raise ValueError(f"Invalid quota type. Must be one of: {[qt.value for qt in QuotaType]}")
        return v


class AdminQuotaStatsResponse(BaseModel):
    """Admin quota statistics response"""
    total_users: int
    active_users: int
    total_daily_quota: float
    total_used_quota: float
    average_usage_percentage: float
    quota_type: str
    stats_date: date


class AdminUserQuotaResponse(BaseModel):
    """Admin user quota details response"""
    user_id: str
    username: str
    email: Optional[str]
    quotas: List[QuotaCurrentResponse]
    total_usage_logs: int
    last_activity: Optional[datetime]


class QuotaMultipleResponse(BaseModel):
    """Response for multiple quota types"""
    user_id: str
    quotas: List[QuotaCurrentResponse]
    last_updated: datetime


# Error Response Models

class QuotaErrorResponse(BaseModel):
    """Error response for quota operations"""
    error: str
    error_code: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Upgrade and Plan Models

class QuotaPlanUpgradeRequest(BaseModel):
    """Request to upgrade quota plan"""
    plan_type: str = Field(description="New plan type (free, basic, pro, enterprise)")
    quota_type: str = Field(default="credits", description="Type of quota")

    @validator('plan_type')
    def validate_plan_type(cls, v):
        valid_plans = ["free", "basic", "pro", "enterprise"]
        if v not in valid_plans:
            raise ValueError(f"Invalid plan type. Must be one of: {valid_plans}")
        return v

    @validator('quota_type')
    def validate_quota_type(cls, v):
        if v not in [qt.value for qt in QuotaType]:
            raise ValueError(f"Invalid quota type. Must be one of: {[qt.value for qt in QuotaType]}")
        return v


class QuotaPlanUpgradeResponse(BaseModel):
    """Response for quota plan upgrade"""
    success: bool
    old_plan: str
    new_plan: str
    old_daily_limit: float
    new_daily_limit: float
    additional_quota_granted: float
    effective_immediately: bool
    message: str