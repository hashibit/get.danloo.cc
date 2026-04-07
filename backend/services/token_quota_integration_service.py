"""
Service for integrating token usage tracking with quota system
Maps tokens to credits and updates user quotas based on actual usage
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from common.database_models.token_usage_model import TokenUsageDB
from backend.services.quota_service import get_quota_service
from common.exceptions.quota_exceptions import QuotaException
from database import get_database

logger = logging.getLogger(__name__)


class TokenQuotaIntegrationService:
    """Service for integrating token usage with quota system"""
    
    def __init__(self):
        self.quota_service = get_quota_service()
        # Token to credits conversion rate (1 credit = 1000 tokens as designed)
        self.tokens_per_credit = 1000.0
    
    def process_token_usage_records(
        self, 
        db: Session, 
        token_usage_records: List[TokenUsageDB],
        user_id: str,
        related_request_uuid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process token usage records and adjust user quotas accordingly
        This handles the precision adjustment between estimated and actual usage
        """
        if not token_usage_records:
            return {
                "success": True,
                "total_tokens": 0,
                "credits_calculated": 0.0,
                "quota_adjustment": 0.0,
                "message": "No token usage to process"
            }
        
        try:
            # Calculate total tokens used across all records
            total_tokens = sum(
                (record.total_tokens or 0) for record in token_usage_records
            )
            
            # Convert tokens to credits
            credits_calculated = total_tokens / self.tokens_per_credit
            
            logger.info(
                f"Processing token usage: {total_tokens} tokens = {credits_calculated:.3f} credits "
                f"for user {user_id}"
            )
            
            # Get current quota to check if adjustment is needed
            current_quota = self.quota_service.get_current_quota_status(db, user_id, "credits")
            
            # Calculate adjustment needed
            # Since we pre-consumed estimated credits, we need to adjust based on actual usage
            quota_adjustment = self._calculate_quota_adjustment(
                db, user_id, credits_calculated, related_request_uuid
            )
            
            adjustment_result = None
            if abs(quota_adjustment) > 0.001:  # Only adjust if difference is significant
                if quota_adjustment > 0:
                    # Actual usage was higher than estimate, consume more credits
                    adjustment_result = self.quota_service.consume_quota(
                        db,
                        user_id=user_id,
                        amount=quota_adjustment,
                        quota_type="credits",
                        related_request_uuid=related_request_uuid,
                        description=f"Additional consumption based on actual token usage: {total_tokens} tokens"
                    )
                    logger.info(f"Consumed additional {quota_adjustment:.3f} credits for user {user_id}")
                else:
                    # Actual usage was lower than estimate, refund credits
                    adjustment_result = self.quota_service.refund_quota(
                        db,
                        user_id=user_id,
                        amount=abs(quota_adjustment),
                        quota_type="credits",
                        related_request_uuid=related_request_uuid,
                        description=f"Refund based on actual token usage: {total_tokens} tokens"
                    )
                    logger.info(f"Refunded {abs(quota_adjustment):.3f} credits to user {user_id}")
            
            return {
                "success": True,
                "total_tokens": total_tokens,
                "credits_calculated": credits_calculated,
                "quota_adjustment": quota_adjustment,
                "adjustment_result": adjustment_result,
                "message": f"Processed {len(token_usage_records)} token usage records"
            }
            
        except QuotaException as e:
            logger.error(f"Quota error processing token usage for user {user_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing token usage for user {user_id}: {str(e)}")
            raise QuotaException(
                f"Failed to process token usage: {str(e)}",
                error_code="TOKEN_QUOTA_INTEGRATION_ERROR"
            )
    
    def _calculate_quota_adjustment(
        self, 
        db: Session, 
        user_id: str, 
        actual_credits: float,
        related_request_uuid: Optional[str] = None
    ) -> float:
        """
        Calculate the quota adjustment needed based on actual vs estimated usage
        """
        try:
            if not related_request_uuid:
                # If no request UUID, assume this is the actual consumption (no pre-consumption)
                return actual_credits
            
            # Find the original consumption record for this request
            from common.database_models.user_quota_model import QuotaUsageLogDB
            
            original_consumption = db.query(QuotaUsageLogDB).filter(
                QuotaUsageLogDB.user_id == user_id,
                QuotaUsageLogDB.related_request_uuid == related_request_uuid,
                QuotaUsageLogDB.operation_type == "consume"
            ).first()
            
            if original_consumption:
                # Calculate difference between actual and estimated
                estimated_credits = float(original_consumption.amount)
                adjustment = actual_credits - estimated_credits
                
                logger.debug(
                    f"Quota adjustment calculation: actual={actual_credits:.3f}, "
                    f"estimated={estimated_credits:.3f}, adjustment={adjustment:.3f}"
                )
                
                return adjustment
            else:
                # No original consumption found, treat as new consumption
                logger.warning(f"No original consumption record found for request {related_request_uuid}")
                return actual_credits
                
        except Exception as e:
            logger.error(f"Error calculating quota adjustment: {str(e)}")
            # If calculation fails, assume actual consumption
            return actual_credits
    
    def batch_process_token_usage(
        self, 
        db: Session, 
        batch_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a batch of token usage records for multiple users/requests
        
        Args:
            batch_records: List of dicts containing:
                - token_usage_records: List[TokenUsageDB]
                - user_id: str
                - related_request_uuid: Optional[str]
        """
        results = []
        successful = 0
        failed = 0
        
        for record_batch in batch_records:
            try:
                result = self.process_token_usage_records(
                    db,
                    record_batch["token_usage_records"],
                    record_batch["user_id"],
                    record_batch.get("related_request_uuid")
                )
                results.append(result)
                successful += 1
                
            except Exception as e:
                logger.error(f"Failed to process token usage batch: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "user_id": record_batch["user_id"]
                })
                failed += 1
        
        return {
            "batch_success": failed == 0,
            "total_batches": len(batch_records),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    def get_credits_from_tokens(self, tokens: int) -> float:
        """Convert tokens to credits using the configured rate"""
        return tokens / self.tokens_per_credit
    
    def get_tokens_from_credits(self, credits: float) -> int:
        """Convert credits to tokens using the configured rate"""
        return int(credits * self.tokens_per_credit)
    
    def estimate_credits_for_request(
        self, 
        estimated_input_tokens: int, 
        estimated_output_tokens: int
    ) -> float:
        """Estimate credits needed for a request based on token estimates"""
        total_tokens = estimated_input_tokens + estimated_output_tokens
        return self.get_credits_from_tokens(total_tokens)
    
    def create_token_usage_summary(
        self, 
        db: Session, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a summary of token usage and credits for a user"""
        try:
            query = db.query(TokenUsageDB).filter(TokenUsageDB.consumer.like(f"%{user_id}%"))
            
            if start_date:
                query = query.filter(TokenUsageDB.create_time >= start_date)
            if end_date:
                query = query.filter(TokenUsageDB.create_time <= end_date)
            
            token_records = query.all()
            
            if not token_records:
                return {
                    "user_id": user_id,
                    "total_records": 0,
                    "total_tokens": 0,
                    "total_credits_equivalent": 0.0,
                    "by_model": {},
                    "period": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    }
                }
            
            # Calculate totals
            total_tokens = sum((record.total_tokens or 0) for record in token_records)
            total_credits = self.get_credits_from_tokens(total_tokens)
            
            # Group by model
            by_model = {}
            for record in token_records:
                model_id = record.model_id
                if model_id not in by_model:
                    by_model[model_id] = {
                        "records": 0,
                        "total_tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "credits_equivalent": 0.0
                    }
                
                by_model[model_id]["records"] += 1
                by_model[model_id]["total_tokens"] += (record.total_tokens or 0)
                by_model[model_id]["input_tokens"] += (record.prompt_tokens or 0)
                by_model[model_id]["output_tokens"] += (record.completion_tokens or 0)
                by_model[model_id]["credits_equivalent"] = self.get_credits_from_tokens(
                    by_model[model_id]["total_tokens"]
                )
            
            return {
                "user_id": user_id,
                "total_records": len(token_records),
                "total_tokens": total_tokens,
                "total_credits_equivalent": round(total_credits, 3),
                "by_model": by_model,
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating token usage summary for user {user_id}: {str(e)}")
            raise


# Singleton instance
_token_quota_integration_service = None

def get_token_quota_integration_service() -> TokenQuotaIntegrationService:
    """Get token quota integration service singleton"""
    global _token_quota_integration_service
    if _token_quota_integration_service is None:
        _token_quota_integration_service = TokenQuotaIntegrationService()
    return _token_quota_integration_service


# Convenience functions
def process_token_usage_for_user(
    user_id: str,
    token_usage_records: List[TokenUsageDB],
    related_request_uuid: Optional[str] = None
) -> Dict[str, Any]:
    """Process token usage records for a user (convenience function)"""
    service = get_token_quota_integration_service()
    db: Session = next(get_database())
    try:
        return service.process_token_usage_records(
            db, token_usage_records, user_id, related_request_uuid
        )
    finally:
        db.close()


def get_user_token_credits_summary(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get token usage and credits summary for a user (convenience function)"""
    service = get_token_quota_integration_service()
    db: Session = next(get_database())
    try:
        return service.create_token_usage_summary(db, user_id, start_date, end_date)
    finally:
        db.close()