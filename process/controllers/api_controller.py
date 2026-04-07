from fastapi import APIRouter, HTTPException, status, Depends
from process.services.job_processor import JobProcessor
from process.services.pellet_generation_service import pellet_generation_service
from typing import Any
from sqlalchemy.orm import Session
from database import get_database
from datetime import datetime, timezone

from common.api_models.process_service import PelletGenerationRequest
from common.database_models.job_model import JobDB

router = APIRouter()
job_processor = JobProcessor()

import logging

logger = logging.getLogger(__name__)


@router.post("/pellet-generation", status_code=status.HTTP_202_ACCEPTED)
async def initiate_pellet_generation(
    pellet_generation_request: PelletGenerationRequest,
    db: Session = Depends(get_database),
):
    """Initiate intelligent pellet generation: M materials -> AI analysis -> N pellets"""
    try:
        # Convert MaterialInfo objects to dict format for service
        user_id = pellet_generation_request.user_id

        # Initiate pellet generation process
        result = pellet_generation_service.initiate_pellet_generation(
            db, pellet_generation_request.materials, user_id
        )

        return {
            "job_id": result["job_id"],
            "status": result["status"],
            "message": result["message"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate pellet generation: {str(e)}"
        )


@router.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_database),
):
    """Get the status of a specific processing job"""
    try:
        job = job_processor.get_job_status(job_id, db)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_database),
):
    """Get the status of a specific processing task"""
    try:
        task = job_processor.get_task_status(task_id, db)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": task.task_id,
            "material_id": task.material_id,
            "status": task.status,
            "result": task.result,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get current scheduler status for monitoring"""
    from services.database_job_scheduler import database_job_scheduler
    
    try:
        status = database_job_scheduler.get_scheduler_status()
        
        # Also add some database statistics
        db: Session = next(get_database())
        pending_jobs_count = db.query(JobDB).filter(JobDB.status == "pending").count()
        in_progress_jobs_count = db.query(JobDB).filter(JobDB.status == "in_progress").count()
        
        status.update({
            "pending_jobs_in_db": pending_jobs_count,
            "in_progress_jobs_in_db": in_progress_jobs_count,
        })
        
        db.close()
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduler status: {str(e)}"
        )


@router.post("/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    from services.database_job_scheduler import database_job_scheduler
    
    try:
        success = database_job_scheduler.cancel_job(job_id)
        
        if success:
            # Also update database status
            db: Session = next(get_database())
            job = db.query(JobDB).filter(JobDB.job_id == job_id).first()
            if job:
                job.status = "cancelled"
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
            db.close()
            
            return {"message": f"Job {job_id} cancelled successfully", "cancelled": True}
        else:
            return {"message": f"Could not cancel job {job_id}", "cancelled": False}
            
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel job: {str(e)}"
        )


@router.post("/job/{job_id}/retry")
async def retry_job(job_id: str):
    """Retry a failed job"""
    from services.database_job_scheduler import database_job_scheduler
    
    try:
        logger.info(f"Retrying job {job_id}")
        
        # Check if job exists and can be retried
        db: Session = next(get_database())
        job = db.query(JobDB).filter(JobDB.job_id == job_id).first()
        
        if not job:
            db.close()
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Only allow retry for failed or cancelled jobs
        if job.status not in ["failed", "cancelled"]:
            db.close()
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot retry job with status '{job.status}'. Only failed or cancelled jobs can be retried."
            )
        
        # Reset job status and error message
        job.status = "pending"
        job.error_message = None
        job.updated_at = datetime.now(timezone.utc)
        
        # Reset all associated tasks to pending status
        from common.database_models.task_model import TaskDB
        tasks = db.query(TaskDB).filter(TaskDB.job_id == job_id).all()
        for task in tasks:
            task.status = "pending"
            task.error_message = None
            task.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.close()
        
        logger.info(f"Job {job_id} reset to pending status, will be picked up by scheduler")
        
        return {
            "message": f"Job {job_id} retried successfully",
            "job_id": job_id,
            "status": "pending",
            "retried_tasks": len(tasks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retry job: {str(e)}"
        )


@router.get("/users/{user_id}/jobs")
async def get_user_jobs(
    user_id: str,
    db: Session = Depends(get_database),
    limit: int = 20,
    offset: int = 0,
):
    """Get all jobs for a specific user - internal endpoint for backend service"""
    logger.info(
        f"[Process Service] Getting jobs for user_id: {user_id}, limit: {limit}, offset: {offset}"
    )
    try:
        jobs = job_processor.get_user_jobs(user_id, db, limit, offset)
        logger.info(f"[Process Service] Found {len(jobs)} jobs for user {user_id}")

        jobs_data = []
        for job in jobs:
            jobs_data.append(
                {
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "user_id": job.user_id,
                    "priority": job.priority,
                    "job_metadata": job.job_metadata,
                    "error_message": job.error_message,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                }
            )

        result = {
            "jobs": jobs_data,
            "total": len(jobs_data),
        }
        logger.info(
            f"[Process Service] Returning {len(jobs_data)} jobs for user {user_id}"
        )
        return result
    except Exception as e:
        logger.error(
            f"[Process Service] Error getting jobs for user {user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get user jobs: {str(e)}"
        )
