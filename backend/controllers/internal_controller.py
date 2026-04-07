"""
Internal API endpoints for service-to-service communication.
These endpoints are not exposed to external clients.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from backend.services.pellet_service import PelletService
from backend.services.secret_service import SecretService
from common.database_models.crypto_keys_model import CryptoKeysDB
from database import get_database
import logging

from common.api_models.pellet_model import (
    BatchPelletCreateFromProcessingRequest,
    BatchPelletCreateFromProcessingResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()
secret_service = SecretService()
pellet_service = PelletService()


@router.get("/crypto-keys/{access_key}")
async def get_crypto_keys_by_access_key(
    access_key: str, db: Session = Depends(get_database)
):
    """
    Get crypto keys by access key (for internal service use).
    Returns the crypto keys needed for Bearer token validation.
    """
    try:
        # Get crypto keys by access key
        crypto_keys_db = (
            db.query(CryptoKeysDB).filter(CryptoKeysDB.access_key == access_key).first()
        )

        if not crypto_keys_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Access key not found"
            )

        # Convert to CryptoKeys format for validation
        crypto_keys_dict = {
            "user_id": crypto_keys_db.user_id,
            "access_key": crypto_keys_db.access_key,
            "secret_key": crypto_keys_db.secret_key,
            "hash_key": crypto_keys_db.hash_key,
            "salt": crypto_keys_db.salt,
            "created_at": crypto_keys_db.created_at.isoformat(),
            "updated_at": crypto_keys_db.updated_at.isoformat(),
        }

        logger.info(f"Retrieved crypto keys for access key {access_key[:10]}...")
        return crypto_keys_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get crypto keys for access key {access_key[:10]}...: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/pellets/batch-create-from-processing",
    response_model=BatchPelletCreateFromProcessingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pellets_from_processing(
    request: BatchPelletCreateFromProcessingRequest, db: Session = Depends(get_database)
):
    """Create multiple pellets from processing service results"""
    try:
        created_pellets = pellet_service.create_pellets_from_processing(db, request)

        return BatchPelletCreateFromProcessingResponse(
            success=True,
            created_count=len(created_pellets),
            pellet_ids=[pellet.id for pellet in created_pellets],
            message=f"Successfully created {len(created_pellets)} pellets",
        )

    except Exception as e:
        logger.error(
            f"Failed to create pellets from processing: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create pellets from processing: {str(e)}",
        )
