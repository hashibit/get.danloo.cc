"""
Admin controller for blacklist management
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.services.blacklist_service import get_blacklist_service, BlacklistEntry
from backend.middleware.auth import get_current_user, require_admin
from backend.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/blacklist", tags=["admin", "blacklist"])


class BlacklistAddRequest(BaseModel):
    """Request model for adding to blacklist"""
    identifier: str
    type: str  # "ip" or "user"
    reason: str
    expires_at: Optional[datetime] = None
    extra_data: Optional[dict] = None


class BlacklistAddRangeRequest(BaseModel):
    """Request model for adding IP range to blacklist"""
    network: str
    reason: str
    expires_at: Optional[datetime] = None
    extra_data: Optional[dict] = None


class BlacklistResponse(BaseModel):
    """Response model for blacklist entries"""
    id: Optional[str]
    identifier: str
    type: str
    reason: str
    created_at: datetime
    expires_at: Optional[datetime]
    created_by: str
    is_active: bool
    extra_data: dict


class BlacklistStatsResponse(BaseModel):
    """Response model for blacklist statistics"""
    total_entries: int
    active_entries: int
    ip_entries: int
    user_entries: int
    expired_entries: int
    expiring_soon: int


@router.post("/add", response_model=BlacklistResponse, status_code=status.HTTP_201_CREATED)
async def add_to_blacklist(
    request: BlacklistAddRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Add entry to blacklist"""
    try:
        blacklist_service = get_blacklist_service()

        entry = blacklist_service.add_to_blacklist(
            identifier=request.identifier,
            entry_type=request.type,
            reason=request.reason,
            created_by=current_user["user_id"],
            expires_at=request.expires_at,
            extra_data=request.extra_data
        )

        logger.info(f"Admin {current_user['user_id']} added {request.type} {request.identifier} to blacklist")

        return BlacklistResponse(
            id=entry.id,
            identifier=entry.identifier,
            type=entry.type,
            reason=entry.reason,
            created_at=entry.created_at,
            expires_at=entry.expires_at,
            created_by=entry.created_by,
            is_active=entry.is_active,
            extra_data=entry.extra_data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding to blacklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add to blacklist")


@router.post("/add-range", response_model=List[BlacklistResponse])
async def add_ip_range_to_blacklist(
    request: BlacklistAddRangeRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Add IP range to blacklist"""
    try:
        blacklist_service = get_blacklist_service()

        entries = blacklist_service.add_ip_range_blacklist(
            network=request.network,
            reason=request.reason,
            created_by=current_user["user_id"],
            expires_at=request.expires_at,
            extra_data=request.extra_data
        )

        logger.info(f"Admin {current_user['user_id']} added IP range {request.network} to blacklist ({len(entries)} entries)")

        return [
            BlacklistResponse(
                id=entry.id,
                identifier=entry.identifier,
                type=entry.type,
                reason=entry.reason,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
                created_by=entry.created_by,
                is_active=entry.is_active,
                extra_data=entry.extra_data
            )
            for entry in entries
        ]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding IP range to blacklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add IP range to blacklist")


@router.delete("/remove", status_code=status.HTTP_200_OK)
async def remove_from_blacklist(
    identifier: str,
    entry_type: str = Query(..., description="Type: 'ip' or 'user'"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Remove entry from blacklist"""
    try:
        blacklist_service = get_blacklist_service()

        success = blacklist_service.remove_from_blacklist(identifier, entry_type)
        if not success:
            raise HTTPException(status_code=404, detail="Entry not found in blacklist")

        logger.info(f"Admin {current_user['user_id']} removed {entry_type} {identifier} from blacklist")

        return {"message": "Entry removed from blacklist successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from blacklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove from blacklist")


@router.get("/list", response_model=List[BlacklistResponse])
async def get_blacklist(
    entry_type: Optional[str] = Query(None, description="Filter by type: 'ip' or 'user'"),
    active_only: bool = Query(True, description="Show only active entries"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Get blacklist entries"""
    try:
        blacklist_service = get_blacklist_service()

        entries = blacklist_service.get_blacklist(entry_type, active_only)

        return [
            BlacklistResponse(
                id=entry.id,
                identifier=entry.identifier,
                type=entry.type,
                reason=entry.reason,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
                created_by=entry.created_by,
                is_active=entry.is_active,
                extra_data=entry.extra_data
            )
            for entry in entries
        ]

    except Exception as e:
        logger.error(f"Error getting blacklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get blacklist")


@router.get("/check")
async def check_blacklist(
    identifier: str,
    entry_type: str = Query(..., description="Type: 'ip' or 'user'"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Check if identifier is blacklisted"""
    try:
        blacklist_service = get_blacklist_service()

        entry = blacklist_service.is_blacklisted(identifier, entry_type)

        if entry:
            return {
                "is_blacklisted": True,
                "entry": {
                    "identifier": entry.identifier,
                    "type": entry.type,
                    "reason": entry.reason,
                    "created_at": entry.created_at,
                    "expires_at": entry.expires_at,
                    "created_by": entry.created_by,
                    "is_active": entry.is_active,
                    "extra_data": entry.extra_data
                }
            }
        else:
            return {"is_blacklisted": False}

    except Exception as e:
        logger.error(f"Error checking blacklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to check blacklist")


@router.get("/stats", response_model=BlacklistStatsResponse)
async def get_blacklist_stats(
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Get blacklist statistics"""
    try:
        blacklist_service = get_blacklist_service()

        stats = blacklist_service.get_blacklist_stats()

        return BlacklistStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting blacklist stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get blacklist stats")


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_expired_blacklist_entries(
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Clean up expired blacklist entries"""
    try:
        blacklist_service = get_blacklist_service()

        cleaned_count = blacklist_service.cleanup_expired_entries()

        logger.info(f"Admin {current_user['user_id']} cleaned up {cleaned_count} expired blacklist entries")

        return {
            "message": f"Cleaned up {cleaned_count} expired entries",
            "cleaned_count": cleaned_count
        }

    except Exception as e:
        logger.error(f"Error cleaning up blacklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cleanup blacklist")


@router.get("/export")
async def export_blacklist(
    entry_type: Optional[str] = Query(None, description="Filter by type: 'ip' or 'user'"),
    active_only: bool = Query(True, description="Show only active entries"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(require_admin)
):
    """Export blacklist entries as JSON"""
    try:
        blacklist_service = get_blacklist_service()

        entries = blacklist_service.get_blacklist(entry_type, active_only)

        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": current_user["user_id"],
            "total_entries": len(entries),
            "entries": [
                {
                    "identifier": entry.identifier,
                    "type": entry.type,
                    "reason": entry.reason,
                    "created_at": entry.created_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                    "created_by": entry.created_by,
                    "is_active": entry.is_active,
                    "extra_data": entry.extra_data
                }
                for entry in entries
            ]
        }

        return export_data

    except Exception as e:
        logger.error(f"Error exporting blacklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export blacklist")