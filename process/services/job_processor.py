import os
import logging
from api_models.material_model import MaterialContentData
from database import get_database

from .material_content_service import material_content_service
from .ai_adapter_service import AIAdapterService

from datetime import datetime, timezone as dt_timezone
import json
from typing import Optional
from sqlalchemy.orm import Session

import httpx

from common.database_models.job_model import JobDB, JobType, JobStatus
from common.database_models.task_model import TaskDB, TaskStatus
from common.database_models.token_usage_model import TokenUsageDB
from common.database_models.object_model import ObjectDB

from common.api_models.ai_provider import (
    ClassificationResult,
    PelletPage,
    KnowledgePoint,
    KnowledgeCategory,
)

from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)


class JobProcessor:
    """
    JobProcessor类负责处理作业和任务的完整流程。

    处理流程概述：
    1. process_job方法接收作业ID和任务ID列表
    2. 更新作业状态为进行中
    3. 使用线程池并发处理每个任务
    4. 等待所有任务完成
    5. 收集已完成任务的结果
    6. 如果没有完成的任务，则将作业标记为失败
    7. 调用AI代理服务(ai-proxy)处理材料分类
    8. 从S3下载分类结果
    9. 将分类结果摘要为pellets
    10. 保存token使用记录
    11. 将pellets数据发送到后端服务
    12. 更新作业状态为已完成，并记录元数据
    13. 如果任何步骤出现异常，则将作业标记为失败
    """
    def __init__(self):
        # AI adapter service for both classification and summarization
        self.ai_adapter = AIAdapterService()

        # Create a thread pool for processing tasks
        self.executor = ThreadPoolExecutor(max_workers=4)

        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000")

    def process_job(
        self,
        job_id: str,
        task_ids: list[str],
        user_id: str,
    ):
        """Process a job asynchronously in a separate thread"""
        db: Session = next(get_database())
        try:
            # Update job status to processing
            job = db.query(JobDB).filter(JobDB.job_id == job_id).first()
            if job:
                job.status = JobStatus.IN_PROGRESS.value
                job.updated_at = datetime.now(dt_timezone.utc)
                db.commit()

            # Process each task concurrently - each task gets its own DB session
            # Create a future for each task
            futures = []
            for task_id in task_ids:
                future = self.executor.submit(self._process_task, task_id)
                futures.append(future)

            # Wait for all tasks to complete
            for future in futures:
                future.result()  # This will raise any exception that occurred in the task

            # Get completed results only - refresh from database
            classification_results = []
            material_contents = []
            for task_id in task_ids:
                # Get fresh task data from database
                fresh_task = db.query(TaskDB).filter(TaskDB.task_id == task_id).first()
                if (
                    fresh_task
                    and fresh_task.status == TaskStatus.COMPLETED.value
                    and fresh_task.result
                ):
                    classification_result = ClassificationResult.model_validate_json(
                        fresh_task.result
                    )
                    classification_results.append(classification_result)

                    material_content: MaterialContentData = (
                        material_content_service.get_material_b64_content_by_id(
                            fresh_task.material_id
                        )
                    )
                    material_contents.append(material_content)

            # If no completed results, mark job as failed
            if not classification_results:
                logger.error(f"All tasks failed for {job_id}, no processed materials.")
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error_message = "All tasks failed during processing"
                    job.updated_at = datetime.now(dt_timezone.utc)
                    db.commit()
                return

            # Step 2: Generate pellets based on AI analysis
            # Prepare summary data and upload to S3
            summary_data = {
                "results": [result.model_dump() for result in classification_results],
                "params": [param.model_dump() for param in material_contents]
            }

            # Save summary data to S3
            s3_bucket = os.getenv("S3_BUCKET", "uploads")
            summary_data_key = f"{user_id}/summary-data/{job_id}/summary-data.json"
            summary_data_json = json.dumps(summary_data)

            material_content_service.write_file_to_s3(
                bucket=s3_bucket,
                key=summary_data_key,
                content=summary_data_json
            )
            logger.info(f"Saved summary data to S3: bucket={s3_bucket}, key={summary_data_key}")

            # Uses the AI adapter service to summarize materials into pellets via proxy
            pellets_data, summary_token_usage_records = self.ai_adapter.summarize_materials_to_pellets_via_proxy(
                summary_data_bucket=s3_bucket,
                summary_data_key=summary_data_key
            )

            # Save token usage records from summary
            if summary_token_usage_records:
                self._save_token_usage_records(summary_token_usage_records, db)

            # Step 3: Create pellets in Backend
            if pellets_data:
                self._create_pellets_in_backend(pellets_data, user_id)

            # Update job status to completed
            if job:
                job.status = JobStatus.COMPLETED.value
                job.updated_at = datetime.now(dt_timezone.utc)

                # Update job metadata
                if not job.job_metadata:
                    job.job_metadata = {}
                job.job_metadata.update(
                    {
                        "pellets_generated": len(pellets_data) if pellets_data else 0,
                        "completed_at": datetime.now(dt_timezone.utc).isoformat(),
                    }
                )
                db.commit()

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
            # Update job status to failed
            job = db.query(JobDB).filter(JobDB.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED.value
                job.error_message = str(e)
                job.updated_at = datetime.now(dt_timezone.utc)
                db.commit()
        finally:
            db.close()

    def _process_task(self, task_id: str):
        """Process a single task using ai-proxy service - each task gets its own DB session
        This method handles the AI classification of individual materials and saves the results."""
        db: Session = next(get_database())
        try:
            # Get fresh task data from database
            task = db.query(TaskDB).filter(TaskDB.task_id == task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found in database")
                return

            # Update task status
            task.status = TaskStatus.IN_PROGRESS.value
            task.updated_at = datetime.now(dt_timezone.utc)
            db.commit()

            # Get object information from database
            obj = db.query(ObjectDB).filter(ObjectDB.id == task.object_id).first()
            if not obj:
                raise Exception(f"Object {task.object_id} not found in database")

            # Process task using AI Proxy
            classification_result, token_usage_record = self._process_task_by_ai_proxy(obj, task_id)

            # Save token usage to database
            self._save_token_usage_records([token_usage_record], db)

            # Update task with result
            task.status = TaskStatus.COMPLETED.value
            task.result = classification_result.model_dump_json()
            task.updated_at = datetime.now(dt_timezone.utc)
            db.commit()

            logger.info(
                f"Task {task.task_id} completed for material {task.material_id} with AI processing"
            )

        except Exception as e:
            # Update task status to failed - get fresh task data again
            task = db.query(TaskDB).filter(TaskDB.task_id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.updated_at = datetime.now(dt_timezone.utc)
                db.commit()
            logger.error(f"Error processing task {task_id}: {str(e)}", exc_info=True)
        finally:
            db.close()

    def _process_task_by_ai_proxy(self, obj: ObjectDB, task_id: str) -> tuple[ClassificationResult, TokenUsageDB]:
        """
        使用AI Proxy处理任务并返回结构化结果
        
        Args:
            obj: ObjectDB对象，包含S3路径信息
            task_id: 任务ID
            
        Returns:
            tuple: (ClassificationResult, TokenUsageDB) 分类结果和token使用记录
        """
        # Call ai-proxy service via ai_adapter
        # Using environment variable for bucket name since ObjectDB doesn't have a bucket field
        s3_bucket = os.getenv("S3_BUCKET", "uploads")

        # Strip bucket prefix from s3_path if present (s3_path may include bucket name)
        object_key = obj.s3_path
        if object_key.startswith(f"{s3_bucket}/"):
            object_key = object_key[len(f"{s3_bucket}/"):]

        result_data = self.ai_adapter.classify_material_via_proxy(
            object_bucket=s3_bucket,
            object_key=object_key
        )
        
        # Get result bucket and key
        result_bucket = result_data["result_bucket"]
        result_key = result_data["result_key"]

        # Download classification result from S3 and get structured data
        logger.info(f"Reading classification results from S3: bucket={result_bucket}, key={result_key}")
        classification_data = material_content_service.read_classification_results_from_s3(
            bucket=result_bucket,
            key=result_key
        )

        # Create ClassificationResult from structured data (only fields that exist in the model)
        classification_result = ClassificationResult(
            knowledge_points=classification_data.knowledge_points,
            language=classification_data.language,
            llm_result={}  # Empty dict for llm_result
        )
        
        # Create token usage record for database
        token_usage_record = TokenUsageDB(
            request_uuid=f"ai-proxy-{task_id}",  # Generate a request UUID
            consumer=f"task:{task_id}",
            model_id=classification_data.metadata.model_id,  # 使用model_id字段
            prompt_tokens=classification_data.metadata.prompt_tokens,
            completion_tokens=classification_data.metadata.completion_tokens,
            total_tokens=classification_data.metadata.total_tokens,
            input_cost=None,  # Not available from ai-proxy
            output_cost=None,  # Not available from ai-proxy
            total_cost=None   # Not available from ai-proxy
        )
        
        logger.info(f"Parsed classification result: {len(classification_data.knowledge_points)} knowledge points, "
                   f"model={classification_data.metadata.model_id}, "  # 使用model_id字段
                   f"tokens={classification_data.metadata.total_tokens} "
                   f"(prompt:{classification_data.metadata.prompt_tokens}, completion:{classification_data.metadata.completion_tokens})")

        return classification_result, token_usage_record

    def _save_token_usage_records(
        self, token_usage_records: list[TokenUsageDB], db: Session
    ) -> None:
        """Save token usage records to database"""
        if not token_usage_records:
            return

        try:
            for record in token_usage_records:
                db.add(record)
            db.commit()
            logger.info(f"Saved {len(token_usage_records)} token usage records to database")
        except Exception as e:
            logger.error(f"Failed to save token usage records to database: {str(e)}")
            db.rollback()

    def _create_pellets_in_backend(
        self, pellets_data: list[PelletPage], user_id: str
    ):
        """
        Create pellets in Backend service
        This method sends the processed pellets data to the backend service via HTTP POST request.
        """
        endpoint_url = (
            f"{self.backend_url}/api/v1/internal/pellets/batch-create-from-processing"
        )
        logger.info(
            f"Creating {len(pellets_data)} pellets in Backend service: {endpoint_url}"
        )
        logger.info(f"User ID: {user_id}")

        # 记录pellets摘要信息
        for i, pellet in enumerate(pellets_data, 1):
            logger.debug(
                f"Pellet {i}: title='{pellet.title[:50]}...', score={pellet.score}"
            )

        try:
            with httpx.Client(timeout=60) as client:
                payload = {
                    "user_id": user_id,
                    "pellets": [pellet.model_dump() for pellet in pellets_data],
                }
                logger.debug(
                    f"Request payload prepared with {len(payload['pellets'])} pellet objects"
                )
                logger.info(
                    f"Request post to /batch-create-from-processing, paylaod: {payload}"
                )

                response = client.post(
                    endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                logger.info(f"Backend service response: status={response.status_code}")

                if response.status_code not in [200, 201]:
                    logger.error(f"Backend pellet creation failed: {response.text}")
                    raise Exception(f"Backend pellet creation failed: {response.text}")

                logger.info(
                    f"Successfully created {len(pellets_data)} pellets in backend"
                )

                # 记录响应信息
                try:
                    response_data = response.json()
                    logger.debug(
                        f"Backend response data keys: {list(response_data.keys())}"
                    )
                except:
                    logger.debug("Backend response is not JSON")

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling Backend service: {str(e)}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"Connection error calling Backend service: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to create pellets in backend: {str(e)}")
            raise

    def get_job_status(self, job_id: str, db: Session) -> Optional[JobDB]:
        """Get the status of a specific job from database"""
        return db.query(JobDB).filter(JobDB.job_id == job_id).first()

    def get_task_status(self, task_id: str, db: Session) -> Optional[TaskDB]:
        """Get the status of a specific task from database"""
        return db.query(TaskDB).filter(TaskDB.task_id == task_id).first()

    def get_user_jobs(
        self, user_id: str, db: Session, limit: int = 20, offset: int = 0
    ) -> list[JobDB]:
        """Get all jobs for a specific user from database"""
        return (
            db.query(JobDB)
            .filter(JobDB.user_id == user_id)
            .order_by(JobDB.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
