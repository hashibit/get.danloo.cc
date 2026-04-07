from sqlalchemy.orm import Session, joinedload

from common.api_models.pellet_model import (
    PelletDB,
    BatchPelletCreateFromProcessingRequest,
)

from common.database_models.pellet_counters_model import PelletCountersDB
from common.database_models.tag_model import TagDB
from common.utils.ulid_utils import generate_ulid
from datetime import datetime, timezone
from typing import List, Optional
import json


class PelletService:

    def create_pellets_from_processing(
        self, db: Session, request: BatchPelletCreateFromProcessingRequest
    ) -> List[PelletDB]:
        """Create multiple pellets from processing service results with enhanced AI fields"""
        created_pellets = []

        for pellet_data in request.pellets:
            pellet_id = generate_ulid()

            # Extract material IDs
            material_ids_str = (
                ",".join(pellet_data.material_ids) if pellet_data.material_ids else None
            )

            # Prepare generation metadata
            generation_metadata = {
                "ai_generated": True,
                "pellet_type": pellet_data.pellet_type,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                "source_materials": pellet_data.material_ids,
            }

            # Create pellet record with new AI fields
            new_pellet = PelletDB(
                id=pellet_id,
                user_id=request.user_id,
                material_ids=material_ids_str,
                title=pellet_data.title,
                content=pellet_data.content,
                status=pellet_data.status,
                ai_score=pellet_data.score,
                pellet_type=pellet_data.pellet_type,
                generation_metadata=json.dumps(generation_metadata),
            )

            db.add(new_pellet)

            # Create counters record
            counters = PelletCountersDB(pellet_id=pellet_id)
            db.add(counters)

            # Process tags from AI generation
            if pellet_data.tags:
                for tag_info in pellet_data.tags:
                    if isinstance(tag_info, dict):
                        tag_name = tag_info.get("name", "")
                        tag_color = tag_info.get("color", "#3b82f6")
                        tag_description = tag_info.get("description", "")

                        # Find or create tag
                        tag = db.query(TagDB).filter(TagDB.name == tag_name).first()
                        if not tag and tag_name:
                            tag = TagDB(
                                id=generate_ulid(),
                                name=tag_name,
                                color=tag_color,
                                description=tag_description,
                            )
                            db.add(tag)
                            db.flush()  # Ensure tag is available for association

                        if tag:
                            new_pellet.tags.append(tag)
                    elif isinstance(tag_info, str):
                        # Handle simple string tags
                        tag = db.query(TagDB).filter(TagDB.name == tag_info).first()
                        if tag:
                            new_pellet.tags.append(tag)

            created_pellets.append(new_pellet)

        if created_pellets:
            db.commit()
            for pellet in created_pellets:
                db.refresh(pellet)

        return created_pellets

    def get_pellet_by_id(self, db: Session, pellet_id: str) -> PelletDB | None:
        """Get pellet by ID from database"""
        return (
            db.query(PelletDB)
            .options(joinedload(PelletDB.tags), joinedload(PelletDB.counters))
            .filter(PelletDB.id == pellet_id)
            .first()
        )

    def get_pellets_by_user(
        self,
        db: Session,
        user_id: str,
        limit: int | None = 10,
        sort_by: str | None = "created_at",
        sort_order: str | None = "desc",
    ) -> list[PelletDB]:
        """Get pellets by user ID from database"""
        query = (
            db.query(PelletDB)
            .options(joinedload(PelletDB.tags), joinedload(PelletDB.counters))
            .filter(PelletDB.user_id == user_id)
        )

        # Apply sorting
        if sort_by == "createdAt" or sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(PelletDB.created_at.desc())
            else:
                query = query.order_by(PelletDB.created_at.asc())
        elif sort_by == "updatedAt" or sort_by == "updated_at":
            if sort_order == "desc":
                query = query.order_by(PelletDB.updated_at.desc())
            else:
                query = query.order_by(PelletDB.updated_at.asc())
        elif sort_by == "title":
            if sort_order == "desc":
                query = query.order_by(PelletDB.title.desc())
            else:
                query = query.order_by(PelletDB.title.asc())

        # Apply limit
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_public_pellets(
        self,
        db: Session,
        limit: Optional[int] = 10,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc",
    ) -> List[PelletDB]:
        """Get public pellets based on visibility field"""
        query = (
            db.query(PelletDB)
            .options(joinedload(PelletDB.tags), joinedload(PelletDB.counters))
            .filter(PelletDB.visibility == "public")
        )

        # Apply sorting
        if sort_by == "createdAt" or sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(PelletDB.created_at.desc())
            else:
                query = query.order_by(PelletDB.created_at.asc())
        elif sort_by == "updatedAt" or sort_by == "updated_at":
            if sort_order == "desc":
                query = query.order_by(PelletDB.updated_at.desc())
            else:
                query = query.order_by(PelletDB.updated_at.asc())
        elif sort_by == "title":
            if sort_order == "desc":
                query = query.order_by(PelletDB.title.desc())
            else:
                query = query.order_by(PelletDB.title.asc())
        elif sort_by == "viewCount":
            # Join with counters for view count sorting
            if sort_order == "desc":
                query = query.join(PelletCountersDB).order_by(
                    PelletCountersDB.view_count.desc()
                )
            else:
                query = query.join(PelletCountersDB).order_by(
                    PelletCountersDB.view_count.asc()
                )

        # Apply limit
        if limit:
            query = query.limit(limit)

        return query.all()

    def mark_as_gold(self, db: Session, pellet_id: str) -> PelletDB:
        """Mark pellet as gold by adding gold tag"""
        pellet = (
            db.query(PelletDB)
            .options(joinedload(PelletDB.tags), joinedload(PelletDB.counters))
            .filter(PelletDB.id == pellet_id)
            .first()
        )
        assert pellet

        # Get or create gold tag
        gold_tag = db.query(TagDB).filter(TagDB.name == "gold").first()
        if not gold_tag:
            # This shouldn't happen if seeded properly, but just in case
            gold_tag = TagDB(
                id="gold",
                name="gold",
                color="yellow",
                description="High quality pellets with golden content",
            )
            db.add(gold_tag)

        # Check if pellet already has gold tag
        if gold_tag not in pellet.tags:
            pellet.tags.append(gold_tag)
            pellet.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(pellet)

        return pellet

    def update_pellet_status(
        self, db: Session, pellet_id: str, status: str
    ) -> PelletDB:
        """Update pellet status in the database"""
        pellet = db.query(PelletDB).filter(PelletDB.id == pellet_id).first()
        assert pellet
        pellet.status = status
        pellet.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(pellet)
        return pellet

    def update_pellet_visibility(
        self, db: Session, pellet_id: str, visibility: str
    ) -> PelletDB:
        """Update pellet visibility in the database"""
        pellet = (
            db.query(PelletDB)
            .options(joinedload(PelletDB.tags), joinedload(PelletDB.counters))
            .filter(PelletDB.id == pellet_id)
            .first()
        )
        assert pellet
        pellet.visibility = visibility
        pellet.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(pellet)
        return pellet


pellet_service = PelletService()
