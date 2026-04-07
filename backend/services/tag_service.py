from sqlalchemy.orm import Session
from common.database_models.tag_model import TagDB
from common.database_models.pellet_model import PelletDB
from common.utils.ulid_utils import generate_ulid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict


class TagCreate(BaseModel):
    name: str
    color: str
    description: str | None = None
    id: str | None = None  # Optional predefined ID for initial data


class TagUpdate(BaseModel):
    name: str
    color: str
    description: str | None = None


class TagService:
    def get_all_tags(self, db: Session) -> list[TagDB]:
        """获取所有标签"""
        return db.query(TagDB).all()

    def get_tag_by_id(self, db: Session, tag_id: str) -> TagDB | None:
        """根据ID获取标签"""
        return db.query(TagDB).filter(TagDB.id == tag_id).first()

    def create_tag(self, db: Session, tag_data: TagCreate) -> TagDB:
        """创建新标签"""
        tag_id = tag_data.id if tag_data.id else generate_ulid()
        tag = TagDB(
            id=tag_id,
            name=tag_data.name,
            color=tag_data.color,
            description=tag_data.description,
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    def update_tag(self, db: Session, tag_id: str, tag_data: TagUpdate) -> TagDB | None:
        """更新标签"""
        tag = db.query(TagDB).filter(TagDB.id == tag_id).first()
        if not tag:
            return None

        if tag_data.name is not None:
            tag.name = tag_data.name
        if tag_data.color is not None:
            tag.color = tag_data.color
        if tag_data.description is not None:
            tag.description = tag_data.description

        tag.updated_at = datetime.now(
            timezone.utc
        )  # This will force an update to the timestamp
        db.commit()
        db.refresh(tag)
        return tag

    def delete_tag(self, db: Session, tag_id: str) -> bool:
        """删除标签"""
        tag = db.query(TagDB).filter(TagDB.id == tag_id).first()
        if not tag:
            return False

        db.delete(tag)
        db.commit()
        return True

    def get_pellets_by_tag(self, db: Session, tag_id: str) -> list[PelletDB]:
        """根据标签获取pellet"""
        return db.query(PelletDB).join(PelletDB.tags).filter(TagDB.id == tag_id).all()

    def add_tag_to_pellet(self, db: Session, pellet_id: str, tag_id: str) -> bool:
        """为pellet添加标签"""
        pellet = db.query(PelletDB).filter(PelletDB.id == pellet_id).first()
        tag = db.query(TagDB).filter(TagDB.id == tag_id).first()

        if not pellet or not tag:
            return False

        if tag not in pellet.tags:
            pellet.tags.append(tag)
            db.commit()
        return True

    def remove_tag_from_pellet(self, db: Session, pellet_id: str, tag_id: str) -> bool:
        """从pellet移除标签"""
        pellet = db.query(PelletDB).filter(PelletDB.id == pellet_id).first()
        tag = db.query(TagDB).filter(TagDB.id == tag_id).first()

        if not pellet or not tag:
            return False

        if tag in pellet.tags:
            pellet.tags.remove(tag)
            db.commit()
        return True


# 创建标签服务实例
tag_service = TagService()
