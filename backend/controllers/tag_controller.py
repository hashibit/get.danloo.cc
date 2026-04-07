from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_database
from common.api_models.tag_model import TagCreate, TagUpdate, TagResponse
from backend.services.tag_service import tag_service

router = APIRouter()


@router.get("/", response_model=list[TagResponse])
def get_all_tags(db: Session = Depends(get_database)):
    """获取所有标签"""
    tags = tag_service.get_all_tags(db)
    return tags


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag_by_id(tag_id: str, db: Session = Depends(get_database)):
    """根据ID获取标签"""
    tag = tag_service.get_tag_by_id(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(tag_data: TagCreate, db: Session = Depends(get_database)):
    """创建新标签"""
    try:
        tag = tag_service.create_tag(db, tag_data)
        return tag
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create tag: {str(e)}")


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: str, tag_data: TagUpdate, db: Session = Depends(get_database)):
    """更新标签"""
    tag = tag_service.update_tag(db, tag_id, tag_data)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: str, db: Session = Depends(get_database)):
    """删除标签"""
    success = tag_service.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return


@router.get("/pellets/{tag_id}", response_model=list)
def get_pellets_by_tag(tag_id: str, db: Session = Depends(get_database)):
    """根据标签获取丹药"""
    pellets = tag_service.get_pellets_by_tag(db, tag_id)
    return pellets


@router.post("/pellets/{pellet_id}/{tag_id}", status_code=status.HTTP_200_OK)
def add_tag_to_pellet(pellet_id: str, tag_id: str, db: Session = Depends(get_database)):
    """为丹药添加标签"""
    success = tag_service.add_tag_to_pellet(db, pellet_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article or tag not found")
    return {"message": "Tag added to pellet successfully"}


@router.delete("/pellets/{pellet_id}/{tag_id}", status_code=status.HTTP_200_OK)
def remove_tag_from_pellet(
    pellet_id: str, tag_id: str, db: Session = Depends(get_database)
):
    """从丹药移除标签"""
    success = tag_service.remove_tag_from_pellet(db, pellet_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article or tag not found")
    return {"message": "Tag removed from pellet successfully"}
