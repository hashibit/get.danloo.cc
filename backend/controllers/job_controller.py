from sys import exc_info
import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging
from database import get_database

from backend.services.processing_service import process_api_base, processing_service, ProcessingServiceError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/jobs")
async def get_user_jobs(
    user_id: str,
    limit: Optional[int] = 20,
    offset: Optional[int] = 0,
    db: Session = Depends(get_database),
):
    """
    Get all jobs for the authenticated user by proxying to process service
    """
    logger.info(
        f"Getting jobs for user_id: {user_id}, limit: {limit}, offset: {offset}"
    )
    try:
        # Construct the URL for process service
        endpoint = f"{process_api_base}/users/{user_id}/jobs"
        params = {"limit": limit, "offset": offset}

        logger.info(
            f"Proxying request to process service: {endpoint} with params: {params}"
        )

        # Make request to process service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            logger.info(f"Process service response: status={response.status_code}")

            if response.status_code == 404:
                logger.info(
                    f"Process service returned 404 for user {user_id} - no jobs found, returning empty list"
                )
                return {"jobs": [], "total": 0}
            elif response.status_code != 200:
                logger.error(
                    f"Process service error: status={response.status_code}, body={response.text}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Process service error: {response.text}",
                )

            jobs_data = response.json()
            logger.info(
                f"Successfully retrieved {len(jobs_data.get('jobs', []))} jobs for user {user_id}"
            )
            return jobs_data

    except httpx.TimeoutException as e:
        logger.error(f"Process service timeout for user {user_id}:", exc_info=e)
        raise HTTPException(status_code=504, detail="Process service timeout")
    except httpx.ConnectError as e:
        logger.error(
            f"Process service connection error for user {user_id}:", exc_info=e
        )
        raise HTTPException(status_code=503, detail="Process service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error getting jobs for user {user_id}:", exc_info=e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get user jobs: {str(e)}"
        )


@router.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_database),
):
    """
    Get the status of a specific job by proxying to process service
    """
    try:
        # Construct the URL for process service
        endpoint = f"{process_api_base}/job/{job_id}"
        logger.info(f"Calling Process service: {endpoint}")

        # Make request to process service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint)

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Job not found")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Process service error: {response.text}",
                )

            return response.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Process service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Process service unavailable")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_database),
):
    """
    Get the status of a specific task by proxying to process service
    """
    try:
        # Construct the URL for process service
        endpoint = f"{process_api_base}/task/{task_id}"
        logger.info(f"Calling Process service: {endpoint}")

        # Make request to process service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint)

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Task not found")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Process service error: {response.text}",
                )

            return response.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Process service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Process service unavailable")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/job/{job_id}/retry")
async def retry_job(
    job_id: str,
    db: Session = Depends(get_database),
):
    """
    Retry a failed job by proxying to process service
    """
    try:
        logger.info(f"Calling Process service to retry job: {job_id}")

        # Use processing service to retry job
        result = await processing_service.retry_job(job_id)
        
        logger.info(f"Successfully retried job {job_id}")
        return result

    except ProcessingServiceError as e:
        logger.error(f"Processing service error retrying job {job_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Job not found")
        elif "cannot retry" in str(e).lower():
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Process service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error retrying job {job_id}:", exc_info=e)
        raise HTTPException(
            status_code=500, detail=f"Failed to retry job: {str(e)}"
        )
