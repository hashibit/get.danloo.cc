import os
import httpx
import logging
from typing import Dict, List, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.services.quota_service import get_quota_service
from common.exceptions.quota_exceptions import QuotaInsufficientException
from database import get_database

logger = logging.getLogger(__name__)

# Call Process service to initiate pellet generation
process_url = os.getenv("PROCESS_SERVICE_URL", "http://process:8001")
process_api_base = process_url + "/api/v1/processing"


class ProcessingServiceError(Exception):
    """Processing service communication error"""
    pass


class ProcessingService:
    """Service for communicating with the Process microservice"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or process_api_base
        self.timeout = 480.0  # 8分钟，足够处理 pellet 生成（最多可能需要6分钟）
        self.quota_service = get_quota_service()
        # Credits needed for processing one material (60k input + 6k output tokens)
        self.credits_per_material = 66.0

    def _prepare_headers(self, token: str = None) -> Dict[str, str]:
        """Prepare request headers"""
        headers = {"Content-Type": "application/json"}
        
        if token and token.strip():
            headers["Authorization"] = f"Bearer {token}"
            logger.debug("Added Authorization header to request")
        else:
            logger.debug("No valid token found, skipping Authorization header")
            
        return headers

    async def create_pellet_generation_job(self, materials_info: List[Dict[str, Any]], user_id: str, token: str = None) -> Dict[str, Any]:
        """Create a pellet generation job in Process service with quota check"""
        endpoint = f"{self.base_url}/pellet-generation"
        
        logger.info(f"Calling Process service: {endpoint}")
        logger.info(f"Request materials count: {len(materials_info)}, user_id: {user_id}")
        
        # Calculate required credits
        required_credits = len(materials_info) * self.credits_per_material
        
        # Check and consume quota before processing
        db: Session = next(get_database())
        try:
            # Check quota availability
            if not self.quota_service.check_quota_sufficient(db, user_id, required_credits):
                available_quota = self.quota_service.get_current_quota_status(db, user_id)
                raise QuotaInsufficientException(
                    f"Insufficient credits for processing {len(materials_info)} materials",
                    required_amount=required_credits,
                    available_amount=available_quota.remaining_amount,
                    quota_type="credits",
                    user_id=user_id
                )
            
            # Consume quota upfront
            consume_result = self.quota_service.consume_quota(
                db,
                user_id=user_id,
                amount=required_credits,
                quota_type="credits",
                description=f"Processing {len(materials_info)} materials"
            )
            
            logger.info(
                f"Consumed {required_credits} credits for user {user_id}, "
                f"remaining: {consume_result.remaining_amount}"
            )
            
        finally:
            db.close()
        
        headers = self._prepare_headers(token)
        payload = {
            "materials": materials_info,
            "user_id": user_id,
            "quota_consumed": required_credits,  # Pass quota info to process service
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                
                logger.info(f"Process service response: status={response.status_code}")
                
                if response.status_code == 202:
                    logger.info("Process service accepted pellet generation request")
                    return response.json()
                else:
                    logger.error(f"Process service returned non-202 status: {response.text}")
                    
                    # Refund quota if processing request failed
                    await self._refund_quota_on_failure(user_id, required_credits, "Processing service rejected request")
                    
                    raise ProcessingServiceError(f"Process service error: {response.text}")
                    
        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling Process service: {str(e)}")
            await self._refund_quota_on_failure(user_id, required_credits, "Processing service timeout")
            raise ProcessingServiceError(f"Process service timeout: {str(e)}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error calling Process service: {str(e)}")
            await self._refund_quota_on_failure(user_id, required_credits, "Processing service unavailable")
            raise ProcessingServiceError(f"Process service unavailable: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Process service request failed: {str(e)}", exc_info=True)
            await self._refund_quota_on_failure(user_id, required_credits, "Processing service request failed")
            raise ProcessingServiceError(f"Process service request failed: {str(e)}")
        except ProcessingServiceError:
            # Already handled above, don't refund again
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Process service: {str(e)}")
            await self._refund_quota_on_failure(user_id, required_credits, "Unexpected error")
            raise ProcessingServiceError(f"Unexpected error: {str(e)}")
    
    async def _refund_quota_on_failure(self, user_id: str, amount: float, reason: str):
        """Refund quota when processing fails"""
        try:
            db: Session = next(get_database())
            try:
                refund_result = self.quota_service.refund_quota(
                    db,
                    user_id=user_id,
                    amount=amount,
                    quota_type="credits",
                    description=f"Refund due to processing failure: {reason}"
                )
                
                logger.info(
                    f"Refunded {amount} credits to user {user_id} due to failure: {reason}, "
                    f"remaining: {refund_result.remaining_amount}"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to refund quota for user {user_id}: {str(e)}")
            # Don't raise here as this is a cleanup operation

    async def get_job_status(self, job_id: str, token: str = None) -> Dict[str, Any]:
        """Get job status from Process service"""
        endpoint = f"{self.base_url}/jobs/{job_id}"
        
        logger.info(f"Getting job status from Process service: {endpoint}")
        
        headers = self._prepare_headers(token)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=headers,
                    timeout=self.timeout,
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise ProcessingServiceError("Job not found")
                else:
                    logger.error(f"Process service returned status {response.status_code}: {response.text}")
                    raise ProcessingServiceError(f"Process service error: {response.text}")
                    
        except httpx.TimeoutException as e:
            logger.error(f"Timeout getting job status: {str(e)}")
            raise ProcessingServiceError(f"Process service timeout: {str(e)}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error getting job status: {str(e)}")
            raise ProcessingServiceError(f"Process service unavailable: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Process service request failed: {str(e)}", exc_info=True)
            raise ProcessingServiceError(f"Process service request failed: {str(e)}")
        except ProcessingServiceError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"Unexpected error getting job status: {str(e)}")
            raise ProcessingServiceError(f"Unexpected error: {str(e)}")

    async def get_user_jobs(self, user_id: str, limit: int = 50, offset: int = 0, token: str = None) -> Dict[str, Any]:
        """Get user jobs from Process service"""
        endpoint = f"{self.base_url}/users/{user_id}/jobs"
        
        logger.info(f"Getting user jobs from Process service: {endpoint}")
        
        headers = self._prepare_headers(token)
        params = {"limit": limit, "offset": offset}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Process service returned status {response.status_code}: {response.text}")
                    raise ProcessingServiceError(f"Process service error: {response.text}")
                    
        except httpx.TimeoutException as e:
            logger.error(f"Timeout getting user jobs: {str(e)}")
            raise ProcessingServiceError(f"Process service timeout: {str(e)}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error getting user jobs: {str(e)}")
            raise ProcessingServiceError(f"Process service unavailable: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Process service request failed: {str(e)}", exc_info=True)
            raise ProcessingServiceError(f"Process service request failed: {str(e)}")
        except ProcessingServiceError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"Unexpected error getting user jobs: {str(e)}")
            raise ProcessingServiceError(f"Unexpected error: {str(e)}")

    async def retry_job(self, job_id: str, token: str = None) -> Dict[str, Any]:
        """Retry a failed job in Process service"""
        endpoint = f"{self.base_url}/job/{job_id}/retry"
        
        logger.info(f"Retrying job in Process service: {endpoint}")
        
        headers = self._prepare_headers(token)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    timeout=self.timeout,
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise ProcessingServiceError("Job not found")
                elif response.status_code == 400:
                    error_data = response.json()
                    raise ProcessingServiceError(error_data.get("detail", "Cannot retry job"))
                else:
                    logger.error(f"Process service returned status {response.status_code}: {response.text}")
                    raise ProcessingServiceError(f"Process service error: {response.text}")
                    
        except httpx.TimeoutException as e:
            logger.error(f"Timeout retrying job: {str(e)}")
            raise ProcessingServiceError(f"Process service timeout: {str(e)}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error retrying job: {str(e)}")
            raise ProcessingServiceError(f"Process service unavailable: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Process service request failed: {str(e)}", exc_info=True)
            raise ProcessingServiceError(f"Process service request failed: {str(e)}")
        except ProcessingServiceError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"Unexpected error retrying job: {str(e)}")
            raise ProcessingServiceError(f"Unexpected error: {str(e)}")


# Singleton instance
processing_service = ProcessingService()
