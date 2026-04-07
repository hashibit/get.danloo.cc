"""
Daily quota reset task for resetting all user quotas
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from backend.services.quota_service import get_quota_service
from database import get_database

logger = logging.getLogger(__name__)


class QuotaResetTask:
    """Task for daily quota reset operations"""
    
    def __init__(self):
        self.quota_service = get_quota_service()
        self.task_name = "quota_reset_task"
    
    def execute(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Execute daily quota reset task"""
        target_date = target_date or date.today()
        start_time = datetime.now()
        
        logger.info(f"Starting daily quota reset for date: {target_date}")
        
        try:
            # Get database session
            db: Session = next(get_database())
            
            try:
                # Perform batch quota reset
                result = self.quota_service.batch_reset_quotas(db, target_date)
                
                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Log results
                logger.info(
                    f"Daily quota reset completed - "
                    f"Date: {target_date}, "
                    f"Reset: {result['reset_count']}, "
                    f"Errors: {result['error_count']}, "
                    f"Duration: {execution_time:.2f}s"
                )
                
                # Return comprehensive result
                return {
                    "task_name": self.task_name,
                    "execution_date": target_date.isoformat(),
                    "execution_time": execution_time,
                    "success": result["success"],
                    "reset_count": result["reset_count"],
                    "error_count": result["error_count"],
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Daily quota reset failed: {str(e)}"
            
            logger.error(error_msg)
            
            return {
                "task_name": self.task_name,
                "execution_date": target_date.isoformat(),
                "execution_time": execution_time,
                "success": False,
                "error": error_msg,
                "reset_count": 0,
                "error_count": 0,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
    
    def execute_for_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Execute quota reset for a range of dates (for backfill)"""
        logger.info(f"Starting quota reset for date range: {start_date} to {end_date}")
        
        results = []
        current_date = start_date
        
        while current_date <= end_date:
            result = self.execute(current_date)
            results.append(result)
            
            # Move to next date
            from datetime import timedelta
            current_date += timedelta(days=1)
        
        # Calculate summary statistics
        total_reset = sum(r.get("reset_count", 0) for r in results)
        total_errors = sum(r.get("error_count", 0) for r in results)
        successful_days = sum(1 for r in results if r.get("success", False))
        
        summary = {
            "task_name": f"{self.task_name}_range",
            "date_range": f"{start_date} to {end_date}",
            "total_days": len(results),
            "successful_days": successful_days,
            "failed_days": len(results) - successful_days,
            "total_reset_count": total_reset,
            "total_error_count": total_errors,
            "daily_results": results
        }
        
        logger.info(
            f"Date range quota reset completed - "
            f"Range: {start_date} to {end_date}, "
            f"Days: {len(results)}, "
            f"Success: {successful_days}/{len(results)}, "
            f"Total Reset: {total_reset}, "
            f"Total Errors: {total_errors}"
        )
        
        return summary


# Singleton instance
_quota_reset_task = None

def get_quota_reset_task() -> QuotaResetTask:
    """Get quota reset task singleton"""
    global _quota_reset_task
    if _quota_reset_task is None:
        _quota_reset_task = QuotaResetTask()
    return _quota_reset_task


# Convenience function for direct execution
def execute_daily_quota_reset(target_date: Optional[date] = None) -> Dict[str, Any]:
    """Execute daily quota reset task (convenience function)"""
    task = get_quota_reset_task()
    return task.execute(target_date)


def execute_quota_reset_backfill(
    start_date: date, 
    end_date: date
) -> Dict[str, Any]:
    """Execute quota reset for date range (convenience function)"""
    task = get_quota_reset_task()
    return task.execute_for_date_range(start_date, end_date)