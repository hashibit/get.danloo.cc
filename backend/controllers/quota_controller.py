from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from common.api_models.user_quota_model import (
    QuotaCurrentResponse, QuotaUsageHistoryResponse, QuotaCheckRequest, 
    QuotaCheckResponse, QuotaConsumeRequest, QuotaRefundRequest,
    QuotaOperationResponse, QuotaMultipleResponse
)
from common.exceptions.quota_exceptions import (
    QuotaException, QuotaInsufficientException, QuotaNotFoundException
)
from backend.services.quota_service import get_quota_service
from backend.services.material_quota_service import get_material_quota_service
from backend.middleware.auth import get_current_user
from common.database_models.user_model import UserDB
from database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
quota_service = get_quota_service()
material_quota_service = get_material_quota_service()


@router.get(
    "/current", 
    response_model=QuotaCurrentResponse,
    summary="Get current quota status",
    description="Get the current quota status for the authenticated user"
)
async def get_current_quota(
    quota_type: str = Query(default="credits", description="Type of quota to query"),
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Get current quota status for user"""
    try:
        quota_status = quota_service.get_current_quota_status(
            db, current_user.id, quota_type
        )
        return quota_status
        
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
        logger.error(f"Error getting quota for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/multiple",
    response_model=QuotaMultipleResponse,
    summary="Get multiple quota types",
    description="Get quota status for multiple quota types"
)
async def get_multiple_quotas(
    quota_types: str = Query(default="credits", description="Comma-separated quota types"),
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Get quota status for multiple quota types"""
    try:
        quota_type_list = [qt.strip() for qt in quota_types.split(",")]
        quotas = []
        
        for quota_type in quota_type_list:
            try:
                quota_status = quota_service.get_current_quota_status(
                    db, current_user.id, quota_type
                )
                quotas.append(quota_status)
            except QuotaNotFoundException:
                # Skip non-existent quota types
                continue
        
        return QuotaMultipleResponse(
            user_id=current_user.id,
            quotas=quotas,
            last_updated=max(q.last_updated for q in quotas) if quotas else None
        )
        
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error getting multiple quotas for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/usage",
    response_model=QuotaUsageHistoryResponse,
    summary="Get quota usage history",
    description="Get paginated quota usage history for the authenticated user"
)
async def get_quota_usage(
    quota_type: str = Query(default="credits", description="Type of quota"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Get quota usage history with pagination"""
    try:
        offset = (page - 1) * page_size
        
        usage_logs = quota_service.get_quota_usage_logs(
            db, current_user.id, quota_type, limit=page_size, offset=offset
        )
        
        # Get total count (simplified - in production might want to optimize this)
        total_logs = quota_service.get_quota_usage_logs(
            db, current_user.id, quota_type, limit=1000, offset=0
        )
        total_count = len(total_logs)
        
        return QuotaUsageHistoryResponse(
            usage_logs=usage_logs,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total_count
        )
        
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error getting quota usage for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/check",
    response_model=QuotaCheckResponse,
    summary="Check quota sufficiency",
    description="Check if user has sufficient quota for a requested amount"
)
async def check_quota(
    request: QuotaCheckRequest,
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Check if user has sufficient quota"""
    try:
        is_sufficient = quota_service.check_quota_sufficient(
            db, current_user.id, request.amount, request.quota_type
        )
        
        current_quota = quota_service.get_current_quota_status(
            db, current_user.id, request.quota_type
        )
        
        return QuotaCheckResponse(
            is_sufficient=is_sufficient,
            current_quota=current_quota,
            requested_amount=request.amount
        )
        
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
        logger.error(f"Error checking quota for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/consume",
    response_model=QuotaOperationResponse,
    summary="Consume quota",
    description="Consume quota for a user operation"
)
async def consume_quota(
    request: QuotaConsumeRequest,
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Consume quota for user operation"""
    try:
        result = quota_service.consume_quota(
            db,
            user_id=current_user.id,
            amount=request.amount,
            quota_type=request.quota_type,
            related_request_uuid=request.related_request_uuid,
            description=request.description
        )
        return result
        
    except QuotaInsufficientException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.to_dict()
        )
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error consuming quota for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/refund",
    response_model=QuotaOperationResponse,
    summary="Refund quota",
    description="Refund quota to user (e.g., after operation failure)"
)
async def refund_quota(
    request: QuotaRefundRequest,
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Refund quota to user"""
    try:
        result = quota_service.refund_quota(
            db,
            user_id=current_user.id,
            amount=request.amount,
            quota_type=request.quota_type,
            related_request_uuid=request.related_request_uuid,
            description=request.description
        )
        return result
        
    except QuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Error refunding quota for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Material Upload Quota Endpoints
@router.get("/material-upload", summary="Get material upload quota")
async def get_material_upload_quota(
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Get current material upload quota information"""
    try:
        quota_info = material_quota_service.get_upload_quota_info(db, current_user.id)
        return {
            "limit": quota_info.limit,
            "used": quota_info.used,
            "remaining": quota_info.remaining,
            "reset_date": quota_info.reset_date.isoformat() if quota_info.reset_date else None,
            "quota_type": quota_info.quota_type,
            "usage_percentage": quota_info.usage_percentage,
            "days_until_reset": quota_info.days_until_reset
        }
    except Exception as e:
        logger.error(f"Error getting material upload quota: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get quota information")


@router.get("/material-upload/check", summary="Check material upload quota")
async def check_material_upload_quota(
    db: Session = Depends(get_database),
    current_user: UserDB = Depends(get_current_user)
):
    """Check if user has quota for material upload"""
    try:
        result = material_quota_service.check_quota_with_info(db, current_user.id)
        
        return {
            "has_quota": result.has_quota,
            "can_upload": result.can_upload,
            "quota_info": {
                "limit": result.quota_info.limit,
                "used": result.quota_info.used,
                "remaining": result.quota_info.remaining,
                "reset_date": result.quota_info.reset_date.isoformat() if result.quota_info.reset_date else None,
                "quota_type": result.quota_info.quota_type,
                "usage_percentage": result.quota_info.usage_percentage,
                "days_until_reset": result.quota_info.days_until_reset
            },
            "message": result.message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking material upload quota: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to check quota")