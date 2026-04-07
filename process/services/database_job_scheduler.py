"""
Database-based job scheduler that polls for pending jobs and processes them
"""

import time
import threading
import logging
from datetime import datetime, timezone
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, Future
from sqlalchemy.orm import Session
from database import get_database

from common.database_models.job_model import JobDB, JobStatus
from common.database_models.task_model import TaskDB, TaskStatus
from process.services.job_processor import JobProcessor

logger = logging.getLogger(__name__)


class DatabaseJobScheduler:
    """Database-based job scheduler that polls for pending jobs and processes them"""

    def __init__(self, max_workers: int = 4, poll_interval: int = 5):
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.running = False
        
        # Create a thread pool for processing jobs
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Job processor instance
        self.job_processor = JobProcessor()
        
        # Track active job futures
        self.active_futures: dict[str, Future] = {}
        
        # Background thread for polling
        self.scheduler_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the scheduler daemon thread"""
        if self.running:
            logger.warning("Database job scheduler is already running")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info(f"Database job scheduler started with {self.max_workers} workers, polling every {self.poll_interval}s")

    def stop(self):
        """Stop the scheduler and wait for all jobs to complete"""
        logger.info("Stopping database job scheduler...")
        self.running = False
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
            
        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Database job scheduler stopped")

    def _poll_loop(self):
        """Main polling loop that checks for pending jobs"""
        logger.info("Database job scheduler polling loop started")
        
        while self.running:
            try:
                # Clean up completed futures first
                self._cleanup_completed_futures()
                
                # Get database session
                db: Session = next(get_database())
                
                # Find pending jobs ordered by priority and creation time
                pending_jobs = (
                    db.query(JobDB)
                    .filter(JobDB.status == JobStatus.PENDING.value)
                    .order_by(JobDB.priority.desc(), JobDB.created_at.asc())  # Higher priority first, then FIFO
                    .limit(self.max_workers)  # Don't get more jobs than we can handle
                    .all()
                )
                
                if pending_jobs:
                    logger.info(f"Found {len(pending_jobs)} pending jobs to process")
                    
                    for job in pending_jobs:
                        # Check if we have capacity to process this job
                        if self._get_active_job_count() >= self.max_workers:
                            logger.debug("All workers busy, skipping additional jobs")
                            break
                            
                        # Get tasks for this job
                        tasks = (
                            db.query(TaskDB)
                            .filter(TaskDB.job_id == job.job_id)
                            .filter(TaskDB.status == TaskStatus.PENDING.value)
                            .all()
                        )
                        
                        if not tasks:
                            logger.warning(f"Job {job.job_id} has no pending tasks, marking as completed")
                            job.status = JobStatus.COMPLETED.value
                            job.updated_at = datetime.now(timezone.utc)
                            db.commit()
                            continue
                            
                        logger.info(f"Processing job {job.job_id} with {len(tasks)} tasks")
                        
                        # Extract task IDs before session closes
                        task_ids = [task.task_id for task in tasks]
                        
                        # Mark job as in progress immediately to prevent duplicate processing
                        job.status = JobStatus.IN_PROGRESS.value
                        job.updated_at = datetime.now(timezone.utc)
                        db.commit()
                        
                        # Submit job to thread pool with task IDs instead of ORM objects
                        future = self.executor.submit(self._process_job_safely, job.job_id, task_ids, job.user_id)
                        self.active_futures[job.job_id] = future
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error in database job scheduler poll loop: {str(e)}", exc_info=True)
                try:
                    if 'db' in locals():
                        db.close()
                except:
                    pass
                    
            # Wait before next poll
            time.sleep(self.poll_interval)

    def _get_active_job_count(self) -> int:
        """Get count of currently active jobs in the executor"""
        return len(self.active_futures)
    
    def _cleanup_completed_futures(self):
        """Clean up completed futures from tracking dictionary"""
        completed_jobs = []
        for job_id, future in self.active_futures.items():
            if future.done():
                completed_jobs.append(job_id)
                try:
                    # Get the result to check for exceptions
                    future.result()
                    logger.debug(f"Job {job_id} completed successfully")
                except Exception as e:
                    logger.error(f"Job {job_id} completed with error: {str(e)}")
        
        # Remove completed futures
        for job_id in completed_jobs:
            del self.active_futures[job_id]

    def _process_job_safely(self, job_id: str, task_ids: list[str], user_id: str):
        """Safely process a job with error handling"""
        try:
            logger.info(f"Starting processing of job {job_id} with {len(task_ids)} tasks")
            
            # Create new database session for this job processing
            db: Session = next(get_database())
            
            try:
                # Fetch fresh task objects in this session
                tasks = (
                    db.query(TaskDB)
                    .filter(TaskDB.task_id.in_(task_ids))
                    .all()
                )
                
                if not tasks:
                    logger.error(f"No tasks found for job {job_id} with IDs: {task_ids}")
                    return
                
                logger.info(f"Loaded {len(tasks)} tasks for job {job_id}")
                
                # Add missing fields to tasks by updating them in the database
                for task in tasks:
                    needs_update = False
                    if not task.object_id:
                        # For backward compatibility, use material_id as object_id if not set
                        task.object_id = task.material_id
                        needs_update = True
                    if not task.content_type:
                        # Default content type
                        task.content_type = 'text'
                        needs_update = True
                    
                    if needs_update:
                        # Update in database to avoid lazy loading issues
                        db.commit()
                        
                # Process the job using existing job processor - pass task IDs
                task_ids_for_processing = [task.task_id for task in tasks]
                self.job_processor.process_job(job_id, task_ids_for_processing, user_id)
                logger.info(f"Successfully completed processing of job {job_id}")
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
            
            # Update job status to failed
            try:
                db: Session = next(get_database())
                job = db.query(JobDB).filter(JobDB.job_id == job_id).first()
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error_message = str(e)
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()
                db.close()
            except Exception as db_error:
                logger.error(f"Failed to update job {job_id} status to failed: {str(db_error)}")

    def get_scheduler_status(self) -> dict:
        """Get current scheduler status for monitoring"""
        return {
            "running": self.running,
            "max_workers": self.max_workers,
            "poll_interval": self.poll_interval,
            "active_jobs": self._get_active_job_count(),
            "active_job_ids": list(self.active_futures.keys()),
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job if possible"""
        if job_id in self.active_futures:
            future = self.active_futures[job_id]
            if future.cancel():
                logger.info(f"Successfully cancelled job {job_id}")
                del self.active_futures[job_id]
                return True
            else:
                logger.warning(f"Could not cancel job {job_id} - already running or completed")
                return False
        else:
            logger.warning(f"Job {job_id} not found in active futures")
            return False


# Global scheduler instance
database_job_scheduler = DatabaseJobScheduler()