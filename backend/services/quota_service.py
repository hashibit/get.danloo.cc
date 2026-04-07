"""
Quota service for managing user quotas and operations
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from common.database_models.user_quota_model import UserQuotaDB, QuotaUsageLogDB
from common.database_models.user_model import UserDB
from common.api_models.user_quota_model import (
    QuotaCurrentResponse,
    QuotaUsageLogResponse,
    QuotaOperationResponse,
)
from common.exceptions.quota_exceptions import (
    QuotaInsufficientException,
    QuotaNotFoundException,
    QuotaServiceException,
    QuotaOperationException,
    QuotaResetException,
    QuotaUpgradeException,
    QuotaConcurrencyException,
)

logger = logging.getLogger(__name__)


class QuotaService:
    """Service for managing user quotas"""

    def __init__(self):
        self.default_quota_type = "credits"
        self.default_daily_limit = (
            660.0  # Default free tier limit - enough for 10 materials per day
        )

    def get_user_quota(
        self, db: Session, user_id: str, quota_type: Optional[str] = None
    ) -> UserQuotaDB:
        """Get user quota record, create if not exists"""
        quota_type = quota_type or self.default_quota_type
        today = date.today()

        try:
            # Try to get existing quota
            quota = (
                db.query(UserQuotaDB)
                .filter(
                    and_(
                        UserQuotaDB.user_id == user_id,
                        UserQuotaDB.quota_type == quota_type,
                        UserQuotaDB.reset_date == today,
                    )
                )
                .first()
            )

            if not quota:
                # Create new quota for today
                quota = self._create_daily_quota(db, user_id, quota_type, today)

            elif quota.is_reset_needed(today):
                # Reset quota if needed
                quota = self._reset_user_quota(db, quota, today)

            return quota

        except Exception as e:
            logger.error(f"Failed to get user quota for user {user_id}: {str(e)}")
            raise QuotaServiceException(
                "Failed to retrieve user quota",
                operation="get_user_quota",
                original_error=e,
            )

    def check_quota_sufficient(
        self, db: Session, user_id: str, amount: float, quota_type: Optional[str] = None
    ) -> bool:
        """Check if user has sufficient quota"""
        try:
            quota = self.get_user_quota(db, user_id, quota_type)
            return quota.is_quota_sufficient(amount)
        except Exception as e:
            logger.error(f"Failed to check quota for user {user_id}: {str(e)}")
            return False

    def consume_quota(
        self,
        db: Session,
        user_id: str,
        amount: float,
        quota_type: Optional[str] = None,
        related_request_uuid: Optional[str] = None,
        description: Optional[str] = None,
    ) -> QuotaOperationResponse:
        """Consume user quota"""
        quota_type = quota_type or self.default_quota_type

        try:
            # Get current quota
            quota = self.get_user_quota(db, user_id, quota_type)

            # Check if sufficient
            if not quota.is_quota_sufficient(amount):
                raise QuotaInsufficientException(
                    f"Insufficient {quota_type} quota",
                    required_amount=amount,
                    available_amount=quota.remaining_amount,
                    quota_type=quota_type,
                    user_id=user_id,
                )

            # Record quota before operation
            quota_before = float(quota.used_amount)

            # Update quota
            quota.used_amount = float(quota.used_amount) + amount
            quota_after = float(quota.used_amount)

            # Create usage log
            log_entry = QuotaUsageLogDB(
                user_id=user_id,
                quota_type=quota_type,
                amount=amount,
                operation_type="consume",
                related_request_uuid=related_request_uuid,
                quota_before=quota_before,
                quota_after=quota_after,
                description=description or f"Consumed {amount} {quota_type}",
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.info(
                f"Consumed quota: user={user_id}, type={quota_type}, "
                f"amount={amount}, remaining={quota.remaining_amount}"
            )

            return QuotaOperationResponse(
                success=True,
                operation_type="consume",
                amount=amount,
                quota_before=quota_before,
                quota_after=quota_after,
                remaining_amount=quota.remaining_amount,
                log_id=log_entry.id,
                timestamp=log_entry.created_at,
            )

        except QuotaInsufficientException:
            # Re-raise quota insufficient exceptions
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Concurrency conflict in quota consumption: ", exc_info=e)
            raise QuotaConcurrencyException(
                "Quota consumption failed due to concurrency conflict",
                user_id=user_id,
                quota_type=quota_type,
                operation_type="consume",
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to consume quota for user {user_id}:", exc_info=e)
            raise QuotaOperationException(
                "Failed to consume quota",
                operation_type="consume",
                amount=amount,
                user_id=user_id,
                original_error=e,
            )

    def refund_quota(
        self,
        db: Session,
        user_id: str,
        amount: float,
        quota_type: Optional[str] = None,
        related_request_uuid: Optional[str] = None,
        description: Optional[str] = None,
    ) -> QuotaOperationResponse:
        """Refund quota to user"""
        quota_type = quota_type or self.default_quota_type

        try:
            # Get current quota
            quota = self.get_user_quota(db, user_id, quota_type)

            # Record quota before operation
            quota_before = float(quota.used_amount)

            # Update quota (don't go below 0)
            quota.used_amount = max(0.0, float(quota.used_amount) - amount)
            quota_after = float(quota.used_amount)

            # Create usage log (negative amount for refund)
            log_entry = QuotaUsageLogDB(
                user_id=user_id,
                quota_type=quota_type,
                amount=-amount,  # Negative for refund
                operation_type="refund",
                related_request_uuid=related_request_uuid,
                quota_before=quota_before,
                quota_after=quota_after,
                description=description or f"Refunded {amount} {quota_type}",
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.info(
                f"Refunded quota: user={user_id}, type={quota_type}, "
                f"amount={amount}, remaining={quota.remaining_amount}"
            )

            return QuotaOperationResponse(
                success=True,
                operation_type="refund",
                amount=amount,
                quota_before=quota_before,
                quota_after=quota_after,
                remaining_amount=quota.remaining_amount,
                log_id=log_entry.id,
                timestamp=log_entry.created_at,
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to refund quota for user {user_id}: {str(e)}")
            raise QuotaOperationException(
                "Failed to refund quota",
                operation_type="refund",
                amount=amount,
                user_id=user_id,
                original_error=e,
            )

    def reset_user_quota(
        self,
        db: Session,
        user_id: str,
        quota_type: Optional[str] = None,
        new_daily_limit: Optional[float] = None,
        description: Optional[str] = None,
    ) -> QuotaOperationResponse:
        """Reset user quota to daily limit"""
        quota_type = quota_type or self.default_quota_type
        today = date.today()

        try:
            # Get current quota
            quota = self.get_user_quota(db, user_id, quota_type)

            # Record quota before operation
            quota_before = float(quota.used_amount)

            # Update quota
            if new_daily_limit is not None:
                quota.daily_limit = new_daily_limit
            quota.used_amount = 0.0
            quota.reset_date = today
            quota_after = 0.0

            # Create usage log
            log_entry = QuotaUsageLogDB(
                user_id=user_id,
                quota_type=quota_type,
                amount=quota_before,  # Amount that was reset
                operation_type="reset",
                quota_before=quota_before,
                quota_after=quota_after,
                description=description or f"Daily quota reset for {quota_type}",
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.info(
                f"Reset quota: user={user_id}, type={quota_type}, "
                f"limit={quota.daily_limit}, date={today}"
            )

            return QuotaOperationResponse(
                success=True,
                operation_type="reset",
                amount=quota_before,
                quota_before=quota_before,
                quota_after=quota_after,
                remaining_amount=quota.remaining_amount,
                log_id=log_entry.id,
                timestamp=log_entry.created_at,
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to reset quota for user {user_id}: {str(e)}")
            raise QuotaResetException(
                "Failed to reset user quota",
                user_id=user_id,
                quota_type=quota_type,
                reset_date=str(today),
                original_error=e,
            )

    def upgrade_user_quota(
        self,
        db: Session,
        user_id: str,
        new_daily_limit: float,
        quota_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> QuotaOperationResponse:
        """Upgrade user quota with immediate effect"""
        quota_type = quota_type or self.default_quota_type

        try:
            # Get current quota
            quota = self.get_user_quota(db, user_id, quota_type)

            # Record old values
            old_limit = float(quota.daily_limit)
            quota_before = float(quota.used_amount)

            # Calculate additional quota to grant immediately
            additional_quota = max(0.0, new_daily_limit - old_limit)

            # Update quota limit
            quota.daily_limit = new_daily_limit

            # Grant additional quota immediately by reducing used_amount
            if additional_quota > 0:
                quota.used_amount = max(
                    0.0, float(quota.used_amount) - additional_quota
                )

            quota_after = float(quota.used_amount)

            # Create usage log
            log_entry = QuotaUsageLogDB(
                user_id=user_id,
                quota_type=quota_type,
                amount=(
                    -additional_quota if additional_quota > 0 else 0
                ),  # Negative = grant
                operation_type="upgrade",
                quota_before=quota_before,
                quota_after=quota_after,
                description=description
                or f"Quota upgraded: {old_limit} -> {new_daily_limit}",
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.info(
                f"Upgraded quota: user={user_id}, type={quota_type}, "
                f"old_limit={old_limit}, new_limit={new_daily_limit}, "
                f"additional_granted={additional_quota}"
            )

            return QuotaOperationResponse(
                success=True,
                operation_type="upgrade",
                amount=additional_quota,
                quota_before=quota_before,
                quota_after=quota_after,
                remaining_amount=quota.remaining_amount,
                log_id=log_entry.id,
                timestamp=log_entry.created_at,
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to upgrade quota for user {user_id}: {str(e)}")
            raise QuotaUpgradeException(
                "Failed to upgrade user quota",
                user_id=user_id,
                old_limit=old_limit if "old_limit" in locals() else 0.0,
                new_limit=new_daily_limit,
                quota_type=quota_type,
                original_error=e,
            )

    def get_quota_usage_logs(
        self,
        db: Session,
        user_id: str,
        quota_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[QuotaUsageLogResponse]:
        """Get user quota usage logs with pagination"""
        quota_type = quota_type or self.default_quota_type

        try:
            query = (
                db.query(QuotaUsageLogDB)
                .filter(
                    and_(
                        QuotaUsageLogDB.user_id == user_id,
                        QuotaUsageLogDB.quota_type == quota_type,
                    )
                )
                .order_by(QuotaUsageLogDB.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

            logs = query.all()
            return [QuotaUsageLogResponse.model_validate(log) for log in logs]

        except Exception as e:
            logger.error(f"Failed to get quota logs for user {user_id}: {str(e)}")
            raise QuotaServiceException(
                "Failed to retrieve quota usage logs",
                operation="get_quota_usage_logs",
                original_error=e,
            )

    def get_current_quota_status(
        self, db: Session, user_id: str, quota_type: Optional[str] = None
    ) -> QuotaCurrentResponse:
        """Get current quota status"""
        try:
            quota = self.get_user_quota(db, user_id, quota_type)

            return QuotaCurrentResponse(
                user_id=quota.user_id,
                quota_type=quota.quota_type,
                daily_limit=float(quota.daily_limit),
                used_amount=float(quota.used_amount),
                remaining_amount=quota.remaining_amount,
                usage_percentage=quota.usage_percentage,
                reset_date=quota.reset_date,
                is_active=quota.is_active,
                last_updated=quota.updated_at,
            )

        except Exception as e:
            logger.error(f"Failed to get quota status for user {user_id}: {str(e)}")
            raise QuotaServiceException(
                "Failed to retrieve quota status",
                operation="get_current_quota_status",
                original_error=e,
            )

    def _create_daily_quota(
        self,
        db: Session,
        user_id: str,
        quota_type: str,
        reset_date: date,
        daily_limit: Optional[float] = None,
    ) -> UserQuotaDB:
        """Create new daily quota record"""
        try:
            # Verify user exists
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                raise QuotaNotFoundException(
                    f"User {user_id} not found", user_id=user_id, quota_type=quota_type
                )

            # Create new quota
            quota = UserQuotaDB(
                user_id=user_id,
                quota_type=quota_type,
                daily_limit=daily_limit or self.default_daily_limit,
                used_amount=0.0,
                reset_date=reset_date,
                is_active=True,
            )

            db.add(quota)
            db.commit()
            db.refresh(quota)

            logger.info(
                f"Created new quota: user={user_id}, type={quota_type}, "
                f"limit={quota.daily_limit}, date={reset_date}"
            )

            return quota

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create quota for user {user_id}: {str(e)}")
            raise

    def _reset_user_quota(
        self, db: Session, quota: UserQuotaDB, new_date: date
    ) -> UserQuotaDB:
        """Reset existing quota to new date"""
        try:
            quota.used_amount = 0.0
            quota.reset_date = new_date

            db.commit()
            db.refresh(quota)

            logger.info(
                f"Reset quota: user={quota.user_id}, type={quota.quota_type}, "
                f"limit={quota.daily_limit}, date={new_date}"
            )

            return quota

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to reset quota {quota.id}: {str(e)}")
            raise

    def batch_reset_quotas(
        self, db: Session, target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Batch reset all user quotas for daily reset task"""
        target_date = target_date or date.today()

        try:
            # Get all quotas that need reset
            quotas_to_reset = (
                db.query(UserQuotaDB).filter(UserQuotaDB.reset_date < target_date).all()
            )

            reset_count = 0
            error_count = 0

            for quota in quotas_to_reset:
                try:
                    # Reset individual quota
                    quota.used_amount = 0.0
                    quota.reset_date = target_date
                    reset_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to reset quota {quota.id}: {str(e)}")

            # Commit all changes
            db.commit()

            logger.info(
                f"Batch quota reset completed: {reset_count} success, "
                f"{error_count} errors, date={target_date}"
            )

            return {
                "reset_count": reset_count,
                "error_count": error_count,
                "target_date": str(target_date),
                "success": error_count == 0,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Batch quota reset failed: {str(e)}")
            raise QuotaServiceException(
                "Batch quota reset failed",
                operation="batch_reset_quotas",
                original_error=e,
            )


# Singleton instance
_quota_service = None


def get_quota_service() -> QuotaService:
    """Get quota service singleton"""
    global _quota_service
    if _quota_service is None:
        _quota_service = QuotaService()
    return _quota_service
