"""
Task scheduler for background tasks like quota reset and monitoring
"""

import logging
import asyncio
import schedule
import threading
from datetime import datetime, time
from typing import Dict, Any, Optional

from backend.tasks.quota_reset_task import execute_daily_quota_reset
from backend.tasks.quota_monitor_task import execute_quota_monitoring

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Background task scheduler using the schedule library"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.tasks_config = {
            "quota_reset": {
                "enabled": True,
                "schedule": "daily",
                "time": "00:00",  # Midnight
                "function": execute_daily_quota_reset,
                "description": "Daily quota reset for all users"
            },
            "quota_monitor": {
                "enabled": True,
                "schedule": "daily", 
                "time": "01:00",  # 1 AM (after reset)
                "function": execute_quota_monitoring,
                "description": "Daily quota usage monitoring and anomaly detection"
            }
        }
    
    def start(self):
        """Start the task scheduler"""
        if self.running:
            logger.warning("Task scheduler is already running")
            return
        
        logger.info("Starting task scheduler")
        
        # Clear any existing scheduled tasks
        schedule.clear()
        
        # Schedule tasks based on configuration
        self._schedule_tasks()
        
        # Start scheduler in background thread
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler,
            name="TaskScheduler",
            daemon=True
        )
        self.scheduler_thread.start()
        
        logger.info("Task scheduler started successfully")
    
    def stop(self):
        """Stop the task scheduler"""
        if not self.running:
            logger.warning("Task scheduler is not running")
            return
        
        logger.info("Stopping task scheduler")
        
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Task scheduler stopped")
    
    def _schedule_tasks(self):
        """Schedule all configured tasks"""
        for task_name, config in self.tasks_config.items():
            if not config.get("enabled", False):
                logger.info(f"Task {task_name} is disabled, skipping")
                continue
            
            try:
                self._schedule_single_task(task_name, config)
                logger.info(
                    f"Scheduled task: {task_name} - {config['schedule']} at {config['time']}"
                )
            except Exception as e:
                logger.error(f"Failed to schedule task {task_name}: {str(e)}")
    
    def _schedule_single_task(self, task_name: str, config: Dict[str, Any]):
        """Schedule a single task based on its configuration"""
        schedule_type = config["schedule"]
        task_time = config["time"]
        task_function = config["function"]
        
        # Wrap the task function to include error handling and logging
        def wrapped_task():
            return self._execute_task(task_name, task_function, config)
        
        if schedule_type == "daily":
            schedule.every().day.at(task_time).do(wrapped_task)
        elif schedule_type == "hourly":
            schedule.every().hour.do(wrapped_task)
        elif schedule_type == "weekly":
            # For weekly tasks, you might want to specify a day
            schedule.every().week.do(wrapped_task)
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
    
    def _execute_task(
        self, 
        task_name: str, 
        task_function, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task with error handling and logging"""
        start_time = datetime.now()
        
        logger.info(f"Executing scheduled task: {task_name}")
        
        try:
            # Execute the task function
            result = task_function()
            
            # Log success
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Task {task_name} completed successfully in {execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            # Log error
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Task {task_name} failed after {execution_time:.2f}s: {str(e)}"
            logger.error(error_msg)
            
            return {
                "task_name": task_name,
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
    
    def _run_scheduler(self):
        """Run the scheduler loop in background thread"""
        logger.info("Task scheduler loop started")
        
        while self.running:
            try:
                schedule.run_pending()
                # Sleep for 1 minute between checks
                threading.Event().wait(60)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                # Continue running even if there's an error
                threading.Event().wait(60)
        
        logger.info("Task scheduler loop stopped")
    
    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """Get information about scheduled tasks"""
        tasks_info = {}
        
        for task_name, config in self.tasks_config.items():
            task_info = {
                "name": task_name,
                "enabled": config.get("enabled", False),
                "schedule": config.get("schedule"),
                "time": config.get("time"),
                "description": config.get("description", ""),
                "next_run": None
            }
            
            # Find next run time from schedule
            for job in schedule.jobs:
                if hasattr(job, 'job_func') and job.job_func.__name__ == 'wrapped_task':
                    # This is a bit hacky but works for getting next run time
                    task_info["next_run"] = job.next_run.isoformat() if job.next_run else None
                    break
            
            tasks_info[task_name] = task_info
        
        return {
            "scheduler_running": self.running,
            "total_tasks": len(self.tasks_config),
            "enabled_tasks": len([c for c in self.tasks_config.values() if c.get("enabled")]),
            "tasks": tasks_info
        }
    
    def execute_task_now(self, task_name: str) -> Dict[str, Any]:
        """Execute a specific task immediately (for testing/manual execution)"""
        if task_name not in self.tasks_config:
            raise ValueError(f"Unknown task: {task_name}")
        
        config = self.tasks_config[task_name]
        task_function = config["function"]
        
        logger.info(f"Manually executing task: {task_name}")
        
        return self._execute_task(task_name, task_function, config)
    
    def update_task_config(self, task_name: str, **kwargs):
        """Update task configuration (requires restart to take effect)"""
        if task_name not in self.tasks_config:
            raise ValueError(f"Unknown task: {task_name}")
        
        # Update configuration
        for key, value in kwargs.items():
            if key in self.tasks_config[task_name]:
                self.tasks_config[task_name][key] = value
        
        logger.info(f"Updated configuration for task {task_name}")
        
        # If scheduler is running, restart to apply changes
        if self.running:
            logger.info("Restarting scheduler to apply configuration changes")
            self.stop()
            self.start()


# Global scheduler instance
_task_scheduler: Optional[TaskScheduler] = None

def get_task_scheduler() -> TaskScheduler:
    """Get the global task scheduler instance"""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler


def start_scheduler():
    """Start the global task scheduler"""
    scheduler = get_task_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global task scheduler"""
    scheduler = get_task_scheduler()
    scheduler.stop()


# Convenience functions for FastAPI startup/shutdown events
async def startup_scheduler():
    """Async wrapper for starting scheduler (for FastAPI startup event)"""
    start_scheduler()


async def shutdown_scheduler():
    """Async wrapper for stopping scheduler (for FastAPI shutdown event)"""
    stop_scheduler()