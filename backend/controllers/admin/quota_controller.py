from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from common.api_models.user_quota_model import (
    AdminQuotaAdjustRequest, AdminQuotaResetRequest, AdminQuotaStatsResponse,
    AdminUserQuotaResponse, QuotaOperationResponse, QuotaCurrentResponse
)
from common.exceptions.quota_exceptions import (
    QuotaException, QuotaNotFoundException
)
from backend.services.quota_service import get_quota_service
from backend.services.user_service import UserService
from backend.middleware.auth import get_current_user  # TODO: Add admin auth
from common.database_models.user_model import UserDB
from database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
quota_service = get_quota_service()
user_service = UserService()


# TODO: Replace with proper admin authentication
def get_admin_user(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    """Temporary admin check - replace with proper admin role check"""
    # For now, treat all authenticated users as admin
    # In production, add proper role-based access control
    return current_user


@router.post(
    "/adjust",
    response_model=QuotaOperationResponse,
    summary="Adjust user quota",
    description="Adjust a user's daily quota limit (admin only)"
)
async def adjust_user_quota(
    request: AdminQuotaAdjustRequest,
    db: Session = Depends(get_database),
    admin_user: UserDB = Depends(get_admin_user)
):
    """Adjust user's daily quota limit"""
    try:
        # Verify target user exists
        target_user = user_service.get_user_by_id(db, request.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )
        
        # Perform quota upgrade
        result = quota_service.upgrade_user_quota(
            db,
            user_id=request.user_id,
            new_daily_limit=request.new_daily_limit,
            quota_type=request.quota_type,
            description=request.reason or f"Admin adjustment by {admin_user.username}"
        )
        
        logger.info(
            f"Admin {admin_user.username} adjusted quota for user {request.user_id}: "
            f"new_limit={request.new_daily_limit}, type={request.quota_type}"
        )
        
        return result
        
    except QuotaNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict()
        )
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error adjusting quota for user {request.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/reset",
    response_model=QuotaOperationResponse,
    summary="Reset user quota",
    description="Reset a user's quota to full daily limit (admin only)"
)
async def reset_user_quota(
    request: AdminQuotaResetRequest,
    db: Session = Depends(get_database),
    admin_user: UserDB = Depends(get_admin_user)
):
    """Reset user's quota"""
    try:
        # Verify target user exists
        target_user = user_service.get_user_by_id(db, request.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )
        
        # Perform quota reset
        result = quota_service.reset_user_quota(
            db,
            user_id=request.user_id,
            quota_type=request.quota_type,
            description=request.reason or f"Admin reset by {admin_user.username}"
        )
        
        logger.info(
            f"Admin {admin_user.username} reset quota for user {request.user_id}: "
            f"type={request.quota_type}"
        )
        
        return result
        
    except QuotaNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict()
        )
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error resetting quota for user {request.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/stats",
    response_model=AdminQuotaStatsResponse,
    summary="Get quota statistics",
    description="Get overall quota usage statistics (admin only)"
)
async def get_quota_stats(
    quota_type: str = Query(default="credits", description="Quota type to analyze"),
    stats_date: Optional[str] = Query(default=None, description="Date for stats (YYYY-MM-DD)"),
    db: Session = Depends(get_database),
    admin_user: UserDB = Depends(get_admin_user)
):
    """Get quota statistics"""
    try:
        # TODO: Implement comprehensive quota statistics
        # This is a simplified version - in production you'd want more sophisticated analytics
        
        target_date = date.fromisoformat(stats_date) if stats_date else date.today()
        
        # Get basic stats from database
        from common.database_models.user_quota_model import UserQuotaDB
        from sqlalchemy import func, and_
        
        # Count users with quotas
        total_users = db.query(func.count(UserQuotaDB.user_id.distinct())).filter(
            and_(
                UserQuotaDB.quota_type == quota_type,
                UserQuotaDB.reset_date == target_date
            )
        ).scalar() or 0
        
        # Count active users (have used some quota)
        active_users = db.query(func.count(UserQuotaDB.user_id.distinct())).filter(
            and_(
                UserQuotaDB.quota_type == quota_type,
                UserQuotaDB.reset_date == target_date,
                UserQuotaDB.used_amount > 0
            )
        ).scalar() or 0
        
        # Sum total daily limits and used amounts
        quota_sums = db.query(
            func.sum(UserQuotaDB.daily_limit),
            func.sum(UserQuotaDB.used_amount)
        ).filter(
            and_(
                UserQuotaDB.quota_type == quota_type,
                UserQuotaDB.reset_date == target_date
            )
        ).first()
        
        total_daily_quota = float(quota_sums[0] or 0)
        total_used_quota = float(quota_sums[1] or 0)
        
        # Calculate average usage percentage
        avg_usage_percentage = 0.0
        if total_daily_quota > 0:
            avg_usage_percentage = (total_used_quota / total_daily_quota) * 100
        
        return AdminQuotaStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_daily_quota=total_daily_quota,
            total_used_quota=total_used_quota,
            average_usage_percentage=round(avg_usage_percentage, 2),
            quota_type=quota_type,
            stats_date=target_date
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting quota stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/user/{user_id}",
    response_model=AdminUserQuotaResponse,
    summary="Get user quota details",
    description="Get detailed quota information for a specific user (admin only)"
)
async def get_user_quota_details(
    user_id: str,
    db: Session = Depends(get_database),
    admin_user: UserDB = Depends(get_admin_user)
):
    """Get detailed quota information for a specific user"""
    try:
        # Verify target user exists
        target_user = user_service.get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Get all quota types for user
        quota_types = ["credits"]  # Add more quota types as needed
        quotas = []
        
        for quota_type in quota_types:
            try:
                quota_status = quota_service.get_current_quota_status(
                    db, user_id, quota_type
                )
                quotas.append(quota_status)
            except QuotaNotFoundException:
                # User doesn't have this quota type, skip
                continue
        
        # Get usage log count
        from common.database_models.user_quota_model import QuotaUsageLogDB
        from sqlalchemy import func
        
        total_usage_logs = db.query(func.count(QuotaUsageLogDB.id)).filter(
            QuotaUsageLogDB.user_id == user_id
        ).scalar() or 0
        
        # Get last activity (most recent quota usage)
        last_log = db.query(QuotaUsageLogDB).filter(
            QuotaUsageLogDB.user_id == user_id
        ).order_by(QuotaUsageLogDB.created_at.desc()).first()
        
        last_activity = last_log.created_at if last_log else None
        
        return AdminUserQuotaResponse(
            user_id=user_id,
            username=target_user.username,
            email=target_user.email,
            quotas=quotas,
            total_usage_logs=total_usage_logs,
            last_activity=last_activity
        )
        
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error getting user quota details for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/batch-reset",
    summary="Batch reset quotas",
    description="Reset quotas for all users (daily reset task, admin only)"
)
async def batch_reset_quotas(
    target_date: Optional[str] = Query(default=None, description="Target date (YYYY-MM-DD)"),
    db: Session = Depends(get_database),
    admin_user: UserDB = Depends(get_admin_user)
):
    """Batch reset quotas for all users"""
    try:
        reset_date = date.fromisoformat(target_date) if target_date else date.today()
        
        result = quota_service.batch_reset_quotas(db, reset_date)
        
        logger.info(
            f"Admin {admin_user.username} triggered batch quota reset: "
            f"date={reset_date}, result={result}"
        )
        
        return {
            "success": result["success"],
            "reset_count": result["reset_count"],
            "error_count": result["error_count"],
            "target_date": result["target_date"],
            "message": f"Reset {result['reset_count']} quotas with {result['error_count']} errors"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error in batch quota reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )