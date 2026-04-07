"""
Security middleware for rate limiting and blacklist checking
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.services.rate_limit_service import get_rate_limit_service
from backend.services.blacklist_service import get_blacklist_service
from backend.database import get_database
from common.utils.request_utils import extract_client_ip

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for rate limiting and blacklist checking"""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_service = get_rate_limit_service()
        self.blacklist_service = get_blacklist_service()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)

        try:
            # Skip security checks for certain paths
            if self._should_skip_security(request):
                return await call_next(request)

            # Blacklist check
            self.blacklist_service.check_request_blacklist(request)

            # Rate limiting check
            self.rate_limit_service.check_api_rate_limit(request)

            # Process request
            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response)

            # Log request for security monitoring
            self._log_security_event(request, response, time.time() - start_time)

            return response

        except HTTPException as e:
            # Handle HTTP exceptions from security checks
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail.get("error", "Security check failed"),
                    "type": e.detail.get("type", "security_error"),
                    "timestamp": time.time(),
                    "client_ip": client_ip
                }
            )
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal security error",
                    "type": "internal_error",
                    "timestamp": time.time()
                }
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        try:
            return extract_client_ip(request)
        except Exception as e:
            logger.warning(f"Failed to extract client IP in security middleware: {e}")
            return "unknown"

    def _should_skip_security(self, request: Request) -> bool:
        """Check if security checks should be skipped for this request"""
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/static",
            "/favicon.ico"
        ]

        # Skip by path
        if any(request.url.path.startswith(path) for path in skip_paths):
            return True

        # Skip OPTIONS requests (CORS)
        if request.method == "OPTIONS":
            return True

        # Skip health checks
        if request.url.path == "/health" or request.url.path == "/ping":
            return True

        return False

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "X-Security-Middleware": "danloo-security"
        }

        for header, value in security_headers.items():
            response.headers[header] = value

    def _log_security_event(self, request: Request, response: Response, duration: float):
        """Log security-related events"""
        client_ip = self._get_client_ip(request)
        status_code = response.status_code

        # Log suspicious activities
        if status_code == 429:  # Too Many Requests
            logger.warning(
                f"Rate limit exceeded - IP: {client_ip}, "
                f"Path: {request.url.path}, "
                f"Method: {request.method}, "
                f"Duration: {duration:.3f}s"
            )

        elif status_code == 403:  # Forbidden
            logger.warning(
                f"Blacklist/block triggered - IP: {client_ip}, "
                f"Path: {request.url.path}, "
                f"Method: {request.method}, "
                f"Duration: {duration:.3f}s"
            )

        elif status_code >= 400:  # All client errors
            logger.info(
                f"Security event - IP: {client_ip}, "
                f"Path: {request.url.path}, "
                f"Method: {request.method}, "
                f"Status: {status_code}, "
                f"Duration: {duration:.3f}s"
            )


class MaterialUploadSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for material upload security checks"""

    def __init__(self, app):
        super().__init__(app)
        from backend.services.material_quota_service import get_material_quota_service
        self.material_quota_service = get_material_quota_service()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process material upload requests with quota checks"""
        # Only apply to material upload endpoints
        if not self._is_material_upload_endpoint(request):
            return await call_next(request)

        try:
            # Check upload quota for authenticated users
            from backend.middleware.auth import get_current_user_optional
            current_user = get_current_user_optional(request)

            if current_user:
                db = next(get_database())
                try:
                    self.material_quota_service.check_upload_quota(db, current_user["user_id"])
                finally:
                    db.close()

            response = await call_next(request)
            return response

        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail.get("error", "Upload quota check failed"),
                    "type": e.detail.get("type", "quota_error"),
                    "timestamp": time.time()
                }
            )
        except Exception as e:
            logger.error(f"Material upload security error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal upload security error",
                    "type": "internal_error",
                    "timestamp": time.time()
                }
            )

    def _is_material_upload_endpoint(self, request: Request) -> bool:
        """Check if request is for material upload"""
        material_upload_paths = [
            "/api/v1/materials",
            "/materials",
            "/api/materials"
        ]

        return (request.method in ["POST", "PUT"] and
                any(request.url.path.startswith(path) for path in material_upload_paths))


# Factory functions for middleware
def create_security_middleware(app):
    """Create security middleware instance"""
    return SecurityMiddleware(app)


def create_material_upload_security_middleware(app):
    """Create material upload security middleware instance"""
    return MaterialUploadSecurityMiddleware(app)
