"""
Material upload quota service for managing material upload limits
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.services.quota_service import get_quota_service
from backend.utils.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)


@dataclass
class MaterialQuotaInfo:
    """Material quota information dataclass"""

    limit: float
    used: float
    remaining: float
    reset_date: Optional[date]
    quota_type: str
    usage_percentage: float
    days_until_reset: Optional[int]

    def __post_init__(self):
        """Calculate derived fields"""
        if self.limit > 0:
            self.usage_percentage = (self.used / self.limit) * 100
        else:
            self.usage_percentage = 0.0

        if self.reset_date:
            self.days_until_reset = (self.reset_date - date.today()).days
        else:
            self.days_until_reset = None


@dataclass
class MaterialQuotaCheckResult:
    """Result of quota check"""

    has_quota: bool
    quota_info: MaterialQuotaInfo
    message: str
    can_upload: bool


class MaterialUploadQuotaService:
    """Service for managing material upload quotas"""

    def __init__(self):
        self.quota_service = get_quota_service()
        self.quota_type = "material_uploads"
        self.default_daily_limit = 500  # 500 materials per day

    def get_quota_service_instance(self):
        """Get quota service instance for testing"""
        return self.quota_service

    @circuit_breaker("material_quota_check", failure_threshold=3, recovery_timeout=30)
    def check_upload_quota(self, db: Session, user_id: str) -> bool:
        """
        Check if user has quota for material upload

        Args:
            db: Database session
            user_id: User ID to check quota for

        Returns:
            bool: True if user has quota available

        Raises:
            HTTPException: If quota exceeded or error occurs
        """
        try:
            # Get current quota
            user_quota = self.quota_service.get_user_quota(db, user_id, self.quota_type)

            # If no quota exists, create one with default limit
            if user_quota.daily_limit == 0:
                user_quota.daily_limit = self.default_daily_limit

            # Check if user has remaining quota
            if user_quota.used_amount >= user_quota.daily_limit:
                quota_info = self.get_upload_quota_info(db, user_id)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Material upload quota exceeded",
                        "type": "material_upload_quota",
                        "limit": quota_info.limit,
                        "used": quota_info.used,
                        "remaining": quota_info.remaining,
                        "reset_time": (
                            quota_info.reset_date.isoformat()
                            if quota_info.reset_date
                            else None
                        ),
                        "usage_percentage": quota_info.usage_percentage,
                    },
                )

            logger.info(
                f"User {user_id} has {user_quota.daily_limit - user_quota.used_amount} uploads remaining"
            )
            return True

        except HTTPException:
            raise
        except Exception as e:
            # If quota doesn't exist, create it
            if "not found" in str(e).lower():
                try:
                    self.quota_service._create_daily_quota(
                        db,
                        user_id,
                        self.quota_type,
                        date.today(),
                        self.default_daily_limit,
                    )
                    logger.info(f"Created default quota for user {user_id}")
                    return True
                except Exception as create_error:
                    logger.error(
                        f"Failed to create quota for user {user_id}: {create_error}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to initialize quota",
                    )

            logger.error(f"Error checking upload quota for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check upload quota",
            )

    @circuit_breaker("material_quota_consume", failure_threshold=3, recovery_timeout=30)
    def consume_upload_quota(self, db: Session, user_id: str, amount: int = 1) -> bool:
        """
        Consume material upload quota

        Args:
            db: Database session
            user_id: User ID to consume quota for
            amount: Amount of quota to consume (default: 1)

        Returns:
            bool: True if quota consumed successfully

        Raises:
            HTTPException: If quota consumption fails
        """
        try:
            self.quota_service.consume_quota(
                db, user_id, amount, self.quota_type, "material_upload"
            )
            logger.info(f"Consumed {amount} material upload quota for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to consume upload quota for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to consume upload quota: {str(e)}",
            )

    def get_upload_quota_info(self, db: Session, user_id: str) -> MaterialQuotaInfo:
        """
        Get current upload quota information

        Args:
            db: Database session
            user_id: User ID to get quota info for

        Returns:
            MaterialQuotaInfo: Quota information
        """
        try:
            user_quota = self.quota_service.get_user_quota(db, user_id, self.quota_type)

            return MaterialQuotaInfo(
                limit=user_quota.daily_limit,
                used=user_quota.used_amount,
                remaining=max(0, user_quota.daily_limit - user_quota.used_amount),
                reset_date=user_quota.reset_date,
                quota_type=self.quota_type,
                usage_percentage=0.0,  # Will be calculated in __post_init__
                days_until_reset=None,  # Will be calculated in __post_init__
            )
        except Exception:
            # Return default if no quota exists
            return MaterialQuotaInfo(
                limit=self.default_daily_limit,
                used=0,
                remaining=self.default_daily_limit,
                reset_date=None,
                quota_type=self.quota_type,
                usage_percentage=0.0,
                days_until_reset=None,
            )

    def check_quota_with_info(
        self, db: Session, user_id: str
    ) -> MaterialQuotaCheckResult:
        """
        Check quota and return detailed information

        Args:
            db: Database session
            user_id: User ID to check quota for

        Returns:
            MaterialQuotaCheckResult: Detailed quota check result
        """
        try:
            quota_info = self.get_upload_quota_info(db, user_id)
            has_quota = quota_info.remaining > 0
            can_upload = has_quota and quota_info.remaining >= 1

            if can_upload:
                message = (
                    f"You have {quota_info.remaining} material uploads remaining today"
                )
            elif has_quota and quota_info.remaining == 0:
                message = (
                    "Daily material upload limit reached. Quota will reset tomorrow."
                )
            else:
                message = "No material upload quota available"

            return MaterialQuotaCheckResult(
                has_quota=has_quota,
                quota_info=quota_info,
                message=message,
                can_upload=can_upload,
            )
        except Exception as e:
            logger.error(f"Error checking quota info for user {user_id}: {e}")
            # Return safe default on error
            default_quota_info = MaterialQuotaInfo(
                limit=self.default_daily_limit,
                used=0,
                remaining=self.default_daily_limit,
                reset_date=None,
                quota_type=self.quota_type,
                usage_percentage=0.0,
                days_until_reset=None,
            )

            return MaterialQuotaCheckResult(
                has_quota=True,
                quota_info=default_quota_info,
                message="Quota information temporarily unavailable",
                can_upload=True,
            )

    def refund_upload_quota(self, db: Session, user_id: str, amount: int = 1) -> bool:
        """
        Refund material upload quota (for failed uploads)

        Args:
            db: Database session
            user_id: User ID to refund quota for
            amount: Amount of quota to refund (default: 1)

        Returns:
            bool: True if quota refunded successfully
        """
        try:
            self.quota_service.refund_quota(
                db, user_id, float(amount), self.quota_type, "material_upload_refund"
            )
            logger.info(f"Refunded {amount} material upload quota for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to refund upload quota for user {user_id}: {e}")
            return False

    def set_user_quota_limit(self, db: Session, user_id: str, daily_limit: int) -> bool:
        """
        Set custom daily quota limit for a user

        Args:
            db: Database session
            user_id: User ID to set quota for
            daily_limit: New daily limit

        Returns:
            bool: True if quota limit set successfully
        """
        try:
            # Get or create user quota
            try:
                user_quota = self.quota_service.get_user_quota(
                    db, user_id, self.quota_type
                )
                user_quota.daily_limit = daily_limit
            except:
                # Create new quota if doesn't exist
                self.quota_service._create_daily_quota(
                    db, user_id, self.quota_type, date.today(), daily_limit
                )

            logger.info(
                f"Set material upload quota limit to {daily_limit} for user {user_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set quota limit for user {user_id}: {e}")
            return False

    def get_quota_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Get overall quota statistics for monitoring

        Args:
            db: Database session

        Returns:
            Dict: Quota statistics
        """
        try:
            # This would need to be implemented in quota_service
            # For now, return basic statistics
            stats = {
                "quota_type": self.quota_type,
                "default_daily_limit": self.default_daily_limit,
                "active_users": 0,  # To be implemented
                "total_daily_capacity": 0,  # To be implemented
                "total_usage_today": 0,  # To be implemented
                "timestamp": datetime.now().isoformat(),
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get quota statistics: {e}")
            return {}


# Global service instance
_material_quota_service = None


def get_material_quota_service() -> MaterialUploadQuotaService:
    """Get material upload quota service instance"""
    global _material_quota_service
    if _material_quota_service is None:
        _material_quota_service = MaterialUploadQuotaService()
    return _material_quota_service
