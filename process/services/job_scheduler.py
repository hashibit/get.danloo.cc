"""
Job scheduling service for managing processing job queue and execution
"""

import time
import threading
from queue import PriorityQueue
from concurrent.futures import ThreadPoolExecutor
from process.services.job_processor import JobProcessor
from sqlalchemy.orm import Session
from common.database_models.task_model import TaskDB, TaskStatus

from datetime import datetime


class JobScheduler:
    """Job scheduler that manages priority queue and task execution"""

    def __init__(self, max_workers: int = 4):
        # Create a thread pool for processing tasks
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        # Create a priority queue for job scheduling
        self.job_queue = PriorityQueue()
        # Start job scheduler thread
        self.scheduler_thread = threading.Thread(target=self._loop, daemon=True)
        self.scheduler_thread.start()

        self.job_processor = JobProcessor()

    def queue_job(
        self,
        priority: int,
        job_id: str,
        tasks: list[TaskDB],
        db: Session,
        callback_url: str = None,
    ):
        """Add job to priority queue"""
        # Lower priority value means higher priority
        self.job_queue.put((-priority, job_id, tasks, db, callback_url))

    def _loop(self):
        """Scheduler that processes jobs from the priority queue"""
        while True:
            try:
                # Get job from priority queue
                priority, job_id, tasks, db, callback_url = self.job_queue.get()
                self.job_processor.process_job(job_id, tasks)

                # Mark task as done in queue
                self.job_queue.task_done()
            except Exception as e:
                print(f"Error in job scheduler: {str(e)}")
                time.sleep(1)  # Wait a bit before continuing to avoid busy loop

    def shutdown(self):
        """Shutdown the scheduler and thread pool"""
        self.executor.shutdown(wait=True)
