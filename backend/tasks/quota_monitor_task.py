"""
Quota monitoring task for tracking usage patterns and generating alerts
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from common.database_models.user_quota_model import UserQuotaDB, QuotaUsageLogDB
from common.database_models.user_model import UserDB
from backend.services.quota_service import get_quota_service
from database import get_database

logger = logging.getLogger(__name__)


class QuotaMonitorTask:
    """Task for monitoring quota usage and generating reports"""
    
    def __init__(self):
        self.quota_service = get_quota_service()
        self.task_name = "quota_monitor_task"
    
    def execute(
        self, 
        target_date: Optional[date] = None,
        generate_report: bool = True,
        check_anomalies: bool = True
    ) -> Dict[str, Any]:
        """Execute quota monitoring task"""
        target_date = target_date or date.today()
        start_time = datetime.now()
        
        logger.info(f"Starting quota monitoring for date: {target_date}")
        
        try:
            db: Session = next(get_database())
            
            try:
                result = {
                    "task_name": self.task_name,
                    "monitoring_date": target_date.isoformat(),
                    "start_time": start_time.isoformat(),
                    "success": True
                }
                
                if generate_report:
                    report = self._generate_usage_report(db, target_date)
                    result["usage_report"] = report
                
                if check_anomalies:
                    anomalies = self._detect_usage_anomalies(db, target_date)
                    result["anomalies"] = anomalies
                
                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()
                result["execution_time"] = execution_time
                result["end_time"] = datetime.now().isoformat()
                
                logger.info(
                    f"Quota monitoring completed - "
                    f"Date: {target_date}, "
                    f"Duration: {execution_time:.2f}s"
                )
                
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Quota monitoring failed: {str(e)}"
            
            logger.error(error_msg)
            
            return {
                "task_name": self.task_name,
                "monitoring_date": target_date.isoformat(),
                "execution_time": execution_time,
                "success": False,
                "error": error_msg,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
    
    def _generate_usage_report(self, db: Session, target_date: date) -> Dict[str, Any]:
        """Generate comprehensive usage report for the target date"""
        try:
            # Basic quota statistics
            quota_stats = db.query(
                func.count(UserQuotaDB.id).label('total_quotas'),
                func.sum(func.coalesce(func.IF(UserQuotaDB.used_amount > 0, 1, 0), 0)).label('active_quotas'),
                func.sum(UserQuotaDB.daily_limit).label('total_daily_limit'),
                func.sum(UserQuotaDB.used_amount).label('total_used'),
                func.avg(UserQuotaDB.used_amount / UserQuotaDB.daily_limit * 100).label('avg_usage_pct')
            ).filter(
                UserQuotaDB.reset_date == target_date
            ).first()
            
            # Usage distribution (group by usage percentage ranges)
            usage_ranges = []
            ranges = [(0, 25), (25, 50), (50, 75), (75, 90), (90, 100), (100, float('inf'))]
            
            for low, high in ranges:
                if high == float('inf'):
                    count = db.query(UserQuotaDB).filter(
                        and_(
                            UserQuotaDB.reset_date == target_date,
                            (UserQuotaDB.used_amount / UserQuotaDB.daily_limit * 100) >= low
                        )
                    ).count()
                    range_name = f"{low}%+"
                else:
                    count = db.query(UserQuotaDB).filter(
                        and_(
                            UserQuotaDB.reset_date == target_date,
                            (UserQuotaDB.used_amount / UserQuotaDB.daily_limit * 100) >= low,
                            (UserQuotaDB.used_amount / UserQuotaDB.daily_limit * 100) < high
                        )
                    ).count()
                    range_name = f"{low}-{high}%"
                
                usage_ranges.append({
                    "range": range_name,
                    "count": count
                })
            
            # Top users by usage
            top_users = db.query(
                UserQuotaDB.user_id,
                UserDB.username,
                UserQuotaDB.daily_limit,
                UserQuotaDB.used_amount,
                (UserQuotaDB.used_amount / UserQuotaDB.daily_limit * 100).label('usage_pct')
            ).join(
                UserDB, UserQuotaDB.user_id == UserDB.id
            ).filter(
                UserQuotaDB.reset_date == target_date
            ).order_by(
                UserQuotaDB.used_amount.desc()
            ).limit(10).all()
            
            top_users_list = [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "daily_limit": float(user.daily_limit),
                    "used_amount": float(user.used_amount),
                    "usage_percentage": float(user.usage_pct or 0)
                }
                for user in top_users
            ]
            
            # Recent activity (last 24 hours of operations)
            yesterday = target_date - timedelta(days=1)
            recent_activity = db.query(
                func.count(QuotaUsageLogDB.id).label('total_operations'),
                func.sum(func.coalesce(
                    func.IF(QuotaUsageLogDB.operation_type == 'consume', 1, 0), 0
                )).label('consume_operations'),
                func.sum(func.coalesce(
                    func.IF(QuotaUsageLogDB.operation_type == 'refund', 1, 0), 0
                )).label('refund_operations'),
                func.sum(func.coalesce(
                    func.IF(QuotaUsageLogDB.operation_type == 'consume', QuotaUsageLogDB.amount, 0), 0
                )).label('total_consumed'),
                func.sum(func.coalesce(
                    func.IF(
                        and_(QuotaUsageLogDB.operation_type == 'refund', QuotaUsageLogDB.amount < 0),
                        QuotaUsageLogDB.amount,
                        0
                    ), 0
                )).label('total_refunded')
            ).filter(
                QuotaUsageLogDB.created_at >= yesterday
            ).first()
            
            return {
                "report_date": target_date.isoformat(),
                "basic_stats": {
                    "total_quotas": quota_stats.total_quotas or 0,
                    "active_quotas": quota_stats.active_quotas or 0,
                    "total_daily_limit": float(quota_stats.total_daily_limit or 0),
                    "total_used": float(quota_stats.total_used or 0),
                    "average_usage_percentage": float(quota_stats.avg_usage_pct or 0)
                },
                "usage_distribution": usage_ranges,
                "top_users": top_users_list,
                "recent_activity": {
                    "total_operations": recent_activity.total_operations or 0,
                    "consume_operations": recent_activity.consume_operations or 0,
                    "refund_operations": recent_activity.refund_operations or 0,
                    "total_consumed": float(recent_activity.total_consumed or 0),
                    "total_refunded": abs(float(recent_activity.total_refunded or 0))
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate usage report: {str(e)}")
            return {"error": str(e)}
    
    def _detect_usage_anomalies(self, db: Session, target_date: date) -> Dict[str, Any]:
        """Detect unusual usage patterns that might indicate issues"""
        try:
            anomalies = {
                "quota_exceeded": [],
                "unusual_refunds": [],
                "inactive_high_limit_users": [],
                "rapid_consumption": []
            }
            
            # 1. Users who have exceeded their quota (shouldn't happen but worth checking)
            exceeded_users = db.query(
                UserQuotaDB.user_id,
                UserDB.username,
                UserQuotaDB.daily_limit,
                UserQuotaDB.used_amount
            ).join(
                UserDB, UserQuotaDB.user_id == UserDB.id
            ).filter(
                and_(
                    UserQuotaDB.reset_date == target_date,
                    UserQuotaDB.used_amount > UserQuotaDB.daily_limit
                )
            ).all()
            
            for user in exceeded_users:
                anomalies["quota_exceeded"].append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "daily_limit": float(user.daily_limit),
                    "used_amount": float(user.used_amount),
                    "overage": float(user.used_amount - user.daily_limit)
                })
            
            # 2. Unusual refund patterns (many refunds might indicate system issues)
            yesterday = target_date - timedelta(days=1)
            high_refund_users = db.query(
                QuotaUsageLogDB.user_id,
                UserDB.username,
                func.count(QuotaUsageLogDB.id).label('refund_count'),
                func.sum(QuotaUsageLogDB.amount).label('total_refunded')
            ).join(
                UserDB, QuotaUsageLogDB.user_id == UserDB.id
            ).filter(
                and_(
                    QuotaUsageLogDB.created_at >= yesterday,
                    QuotaUsageLogDB.operation_type == 'refund'
                )
            ).group_by(
                QuotaUsageLogDB.user_id, UserDB.username
            ).having(
                func.count(QuotaUsageLogDB.id) > 5  # More than 5 refunds
            ).all()
            
            for user in high_refund_users:
                anomalies["unusual_refunds"].append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "refund_count": user.refund_count,
                    "total_refunded": abs(float(user.total_refunded))
                })
            
            # 3. High-limit users with no activity (potential waste)
            inactive_high_users = db.query(
                UserQuotaDB.user_id,
                UserDB.username,
                UserQuotaDB.daily_limit,
                UserQuotaDB.used_amount
            ).join(
                UserDB, UserQuotaDB.user_id == UserDB.id
            ).filter(
                and_(
                    UserQuotaDB.reset_date == target_date,
                    UserQuotaDB.daily_limit > 500,  # High limit
                    UserQuotaDB.used_amount == 0    # No usage
                )
            ).all()
            
            for user in inactive_high_users:
                anomalies["inactive_high_limit_users"].append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "daily_limit": float(user.daily_limit),
                    "used_amount": float(user.used_amount)
                })
            
            # 4. Rapid consumption in short time (potential abuse or system issue)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            rapid_consumers = db.query(
                QuotaUsageLogDB.user_id,
                UserDB.username,
                func.count(QuotaUsageLogDB.id).label('operation_count'),
                func.sum(QuotaUsageLogDB.amount).label('total_consumed')
            ).join(
                UserDB, QuotaUsageLogDB.user_id == UserDB.id
            ).filter(
                and_(
                    QuotaUsageLogDB.created_at >= one_hour_ago,
                    QuotaUsageLogDB.operation_type == 'consume'
                )
            ).group_by(
                QuotaUsageLogDB.user_id, UserDB.username
            ).having(
                func.sum(QuotaUsageLogDB.amount) > 100  # More than 100 credits in 1 hour
            ).all()
            
            for user in rapid_consumers:
                anomalies["rapid_consumption"].append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "operation_count": user.operation_count,
                    "total_consumed": float(user.total_consumed),
                    "time_window": "1 hour"
                })
            
            # Calculate total anomaly count
            total_anomalies = sum(len(v) for v in anomalies.values())
            anomalies["summary"] = {
                "total_anomalies": total_anomalies,
                "anomaly_types": len([k for k, v in anomalies.items() if v and k != "summary"])
            }
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect usage anomalies: {str(e)}")
            return {"error": str(e)}


# Singleton instance
_quota_monitor_task = None

def get_quota_monitor_task() -> QuotaMonitorTask:
    """Get quota monitor task singleton"""
    global _quota_monitor_task
    if _quota_monitor_task is None:
        _quota_monitor_task = QuotaMonitorTask()
    return _quota_monitor_task


# Convenience function for direct execution
def execute_quota_monitoring(
    target_date: Optional[date] = None,
    generate_report: bool = True,
    check_anomalies: bool = True
) -> Dict[str, Any]:
    """Execute quota monitoring task (convenience function)"""
    task = get_quota_monitor_task()
    return task.execute(target_date, generate_report, check_anomalies)