from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.services.material_service import material_service
from backend.services.material_quota_service import get_material_quota_service
from backend.middleware.auth import get_current_user

from database import get_database

from common.database_models.material_model import MaterialDB
from common.api_models.material_model import (
    MaterialData,
    MaterialListResponse,
    MaterialFromObjectCreate,
    MaterialFromUrlCreate,
    MaterialFromTextCreate,
)


router = APIRouter()
material_quota_service = get_material_quota_service()


@router.get("/", response_model=MaterialListResponse)
async def get_materials(
    limit: int | None = 10,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get materials list for current user"""
    try:
        materials = material_service.get_materials_by_user(
            db, current_user["user_id"], limit=limit
        )
        material_datas = [MaterialData.model_validate(m) for m in materials]
        return MaterialListResponse(
            materials=material_datas,
            pagination={"limit": limit, "offset": 0, "total": len(materials)},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{material_id}", response_model=MaterialData)
async def get_material(
    material_id: str,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get material by ID"""
    try:
        material = material_service.get_material_by_id(db, material_id)
        if material is None:
            raise HTTPException(status_code=404, detail="Material not found")

        # Check if user owns the material
        if material.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return material
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/from-object", response_model=MaterialData, status_code=status.HTTP_201_CREATED
)
async def create_material_from_object(
    data: MaterialFromObjectCreate,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Create material from uploaded file object"""
    try:
        # Check material upload quota
        material_quota_service.check_upload_quota(db, current_user["user_id"])

        material = material_service.create_material_from_object(
            db, current_user["user_id"], data
        )

        # Consume upload quota
        material_quota_service.consume_upload_quota(db, current_user["user_id"], 1)

        return material
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/from-url", response_model=MaterialData, status_code=status.HTTP_201_CREATED
)
async def create_material_from_url(
    data: MaterialFromUrlCreate,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Create material from URL by fetching content"""
    try:
        # Check material upload quota
        material_quota_service.check_upload_quota(db, current_user["user_id"])

        material = await material_service.create_material_from_url(
            db, current_user["user_id"], data
        )

        # Consume upload quota
        material_quota_service.consume_upload_quota(db, current_user["user_id"], 1)

        return material
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/from-text", response_model=MaterialData, status_code=status.HTTP_201_CREATED
)
async def create_material_from_text(
    data: MaterialFromTextCreate,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Create material from text content"""
    try:
        # Check material upload quota
        material_quota_service.check_upload_quota(db, current_user["user_id"])

        material = await material_service.create_material_from_text(
            db, current_user["user_id"], data
        )

        # Consume upload quota
        material_quota_service.consume_upload_quota(db, current_user["user_id"], 1)

        return material
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
