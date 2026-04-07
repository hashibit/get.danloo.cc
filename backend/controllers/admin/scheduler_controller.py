from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from backend.scheduler import get_task_scheduler
from backend.middleware.auth import get_current_user
from common.database_models.user_model import UserDB
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# TODO: Replace with proper admin authentication
def get_admin_user(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    """Temporary admin check - replace with proper admin role check"""
    return current_user


@router.get(
    "/status",
    summary="Get scheduler status",
    description="Get current status and configuration of the task scheduler (admin only)"
)
async def get_scheduler_status(
    admin_user: UserDB = Depends(get_admin_user)
):
    """Get task scheduler status"""
    try:
        scheduler = get_task_scheduler()
        status_info = scheduler.get_scheduled_tasks()
        
        logger.info(f"Admin {admin_user.username} requested scheduler status")
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduler status"
        )


@router.post(
    "/execute/{task_name}",
    summary="Execute task immediately",
    description="Execute a specific task immediately (admin only)"
)
async def execute_task_now(
    task_name: str,
    admin_user: UserDB = Depends(get_admin_user)
):
    """Execute a task immediately"""
    try:
        scheduler = get_task_scheduler()
        result = scheduler.execute_task_now(task_name)
        
        logger.info(
            f"Admin {admin_user.username} manually executed task: {task_name}"
        )
        
        return {
            "message": f"Task {task_name} executed",
            "result": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error executing task {task_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task {task_name}"
        )


@router.post(
    "/start",
    summary="Start task scheduler",
    description="Start the task scheduler (admin only)"
)
async def start_scheduler(
    admin_user: UserDB = Depends(get_admin_user)
):
    """Start the task scheduler"""
    try:
        scheduler = get_task_scheduler()
        scheduler.start()
        
        logger.info(f"Admin {admin_user.username} started the task scheduler")
        
        return {"message": "Task scheduler started"}
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start scheduler"
        )


@router.post(
    "/stop",
    summary="Stop task scheduler",
    description="Stop the task scheduler (admin only)"
)
async def stop_scheduler(
    admin_user: UserDB = Depends(get_admin_user)
):
    """Stop the task scheduler"""
    try:
        scheduler = get_task_scheduler()
        scheduler.stop()
        
        logger.info(f"Admin {admin_user.username} stopped the task scheduler")
        
        return {"message": "Task scheduler stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop scheduler"
        )


@router.put(
    "/task/{task_name}/config",
    summary="Update task configuration",
    description="Update configuration for a specific task (admin only)"
)
async def update_task_config(
    task_name: str,
    config: Dict[str, Any],
    admin_user: UserDB = Depends(get_admin_user)
):
    """Update task configuration"""
    try:
        scheduler = get_task_scheduler()
        
        # Update task configuration
        scheduler.update_task_config(task_name, **config)
        
        logger.info(
            f"Admin {admin_user.username} updated config for task {task_name}: {config}"
        )
        
        return {
            "message": f"Task {task_name} configuration updated",
            "config": config
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating task config for {task_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task {task_name} configuration"
        )