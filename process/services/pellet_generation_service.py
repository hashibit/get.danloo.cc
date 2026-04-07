"""
Pellet Generation Service

Handles intelligent pellet generation from materials using AI analysis.
M materials -> AI analysis -> N pellets (where N can be 0, 1, or multiple)
"""

import os
from typing import Any
from sqlalchemy.orm import Session
from common.utils.ulid_utils import generate_ulid
import logging

from common.api_models.process_service import MaterialInfo
from common.database_models.job_model import (
    JobDB,
    JobType,
    JobStatus,
)

from common.database_models.task_model import (
    TaskDB,
    TaskStatus,
)

from common.database_models.material_model import MaterialDB
from process.services.material_content_service import material_content_service

logger = logging.getLogger(__name__)


class PelletGenerationService:
    def __init__(self):
        self.ai_provider_url = os.getenv("AI_PROVIDER_URL", "http://ai-provider:8002")
        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000")

    def initiate_pellet_generation(
        self, db: Session, materials_info: list[MaterialInfo], user_id: str
    ) -> dict[str, Any]:
        """
        Initiate intelligent pellet generation from materials

        Args:
            db: Database session
            materials: list of material data to process
            user_id: User ID for ownership

        Returns:
            dict with job_id, status, and message
        """

        materials: list[MaterialDB] = []
        for m in materials_info:
            material_info = material_content_service.get_material_info(m.id)
            assert material_info, f"material {m.id} must exist in database."
            materials.append(material_info)

        try:
            # Create processing job
            job_id = generate_ulid()
            job = JobDB(
                job_id=job_id,
                job_type=JobType.PELLET_GENERATION,
                status=JobStatus.PENDING,
                user_id=user_id,
                job_metadata={
                    "material_count": len(materials),
                    "materials": [{"id": m.id} for m in materials],
                },
            )
            db.add(job)

            tasks = []

            # Create tasks for each material
            for material in materials:
                task_id = generate_ulid()
                task = TaskDB(
                    task_id=task_id,
                    job_id=job_id,
                    material_id=material.id,
                    object_id=material.object_id,
                    content_type=material.content_type,
                    status=TaskStatus.PENDING,
                    task_type="ANALYZE_MATERIAL",
                )
                tasks.append(task)
                db.add(task)

            db.commit()

            # Job is now in database with PENDING status
            # The database job scheduler will pick it up automatically
            logger.info(
                f"Created job {job_id} with {len(tasks)} tasks, waiting for scheduler to process"
            )

            return {
                "job_id": job_id,
                "status": "accepted",
                "message": f"AI炼丹师开始分析 {len(materials_info)} 种材料",
            }

        except Exception as e:
            logger.error(f"Failed to initiate pellet generation: {str(e)}")
            db.rollback()
            raise


# Global service instance
pellet_generation_service = PelletGenerationService()
