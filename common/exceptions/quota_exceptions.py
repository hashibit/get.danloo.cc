"""Quota system exceptions"""

from typing import Optional


class QuotaException(Exception):
    """Base quota exception"""
    
    def __init__(self, message: str, error_code: str = "QUOTA_ERROR", details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API response"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class QuotaInsufficientException(QuotaException):
    """Raised when user quota is insufficient for the requested operation"""
    
    def __init__(
        self, 
        message: str = "Insufficient quota", 
        required_amount: float = 0.0,
        available_amount: float = 0.0,
        quota_type: str = "credits",
        user_id: Optional[str] = None
    ):
        details = {
            "required_amount": required_amount,
            "available_amount": available_amount,
            "quota_type": quota_type,
            "shortage": max(0, required_amount - available_amount)
        }
        if user_id:
            details["user_id"] = user_id
            
        super().__init__(message, "QUOTA_INSUFFICIENT", details)
        self.required_amount = required_amount
        self.available_amount = available_amount
        self.quota_type = quota_type
        self.user_id = user_id


class QuotaNotFoundException(QuotaException):
    """Raised when user quota record is not found"""
    
    def __init__(
        self, 
        message: str = "Quota not found", 
        user_id: Optional[str] = None,
        quota_type: str = "credits"
    ):
        details = {"quota_type": quota_type}
        if user_id:
            details["user_id"] = user_id
            
        super().__init__(message, "QUOTA_NOT_FOUND", details)
        self.user_id = user_id
        self.quota_type = quota_type


class QuotaServiceException(QuotaException):
    """Raised when quota service encounters an internal error"""
    
    def __init__(
        self, 
        message: str = "Quota service error", 
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if original_error:
            details["original_error"] = str(original_error)
            details["original_error_type"] = type(original_error).__name__
            
        super().__init__(message, "QUOTA_SERVICE_ERROR", details)
        self.operation = operation
        self.original_error = original_error


class QuotaOperationException(QuotaException):
    """Raised when a quota operation (consume/refund) fails"""
    
    def __init__(
        self, 
        message: str = "Quota operation failed", 
        operation_type: Optional[str] = None,
        amount: float = 0.0,
        user_id: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        details = {
            "amount": amount
        }
        if operation_type:
            details["operation_type"] = operation_type
        if user_id:
            details["user_id"] = user_id
        if original_error:
            details["original_error"] = str(original_error)
            
        super().__init__(message, "QUOTA_OPERATION_FAILED", details)
        self.operation_type = operation_type
        self.amount = amount
        self.user_id = user_id
        self.original_error = original_error


class QuotaResetException(QuotaException):
    """Raised when quota reset operation fails"""
    
    def __init__(
        self, 
        message: str = "Quota reset failed", 
        user_id: Optional[str] = None,
        quota_type: str = "credits",
        reset_date: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        details = {"quota_type": quota_type}
        if user_id:
            details["user_id"] = user_id
        if reset_date:
            details["reset_date"] = reset_date
        if original_error:
            details["original_error"] = str(original_error)
            
        super().__init__(message, "QUOTA_RESET_FAILED", details)
        self.user_id = user_id
        self.quota_type = quota_type
        self.reset_date = reset_date
        self.original_error = original_error


class QuotaUpgradeException(QuotaException):
    """Raised when quota upgrade operation fails"""
    
    def __init__(
        self, 
        message: str = "Quota upgrade failed", 
        user_id: Optional[str] = None,
        old_limit: float = 0.0,
        new_limit: float = 0.0,
        quota_type: str = "credits",
        original_error: Optional[Exception] = None
    ):
        details = {
            "old_limit": old_limit,
            "new_limit": new_limit,
            "quota_type": quota_type
        }
        if user_id:
            details["user_id"] = user_id
        if original_error:
            details["original_error"] = str(original_error)
            
        super().__init__(message, "QUOTA_UPGRADE_FAILED", details)
        self.user_id = user_id
        self.old_limit = old_limit
        self.new_limit = new_limit
        self.quota_type = quota_type
        self.original_error = original_error


class QuotaConcurrencyException(QuotaException):
    """Raised when quota operation fails due to concurrency issues"""
    
    def __init__(
        self, 
        message: str = "Quota concurrency conflict", 
        user_id: Optional[str] = None,
        quota_type: str = "credits",
        operation_type: Optional[str] = None
    ):
        details = {"quota_type": quota_type}
        if user_id:
            details["user_id"] = user_id
        if operation_type:
            details["operation_type"] = operation_type
            
        super().__init__(message, "QUOTA_CONCURRENCY_ERROR", details)
        self.user_id = user_id
        self.quota_type = quota_type
        self.operation_type = operation_type


class QuotaValidationException(QuotaException):
    """Raised when quota request validation fails"""
    
    def __init__(
        self, 
        message: str = "Quota validation failed", 
        field: Optional[str] = None,
        value: Optional[str] = None,
        constraint: Optional[str] = None
    ):
        details = {}
        if field:
            details["field"] = field
        if value:
            details["value"] = value
        if constraint:
            details["constraint"] = constraint
            
        super().__init__(message, "QUOTA_VALIDATION_ERROR", details)
        self.field = field
        self.value = value
        self.constraint = constraint