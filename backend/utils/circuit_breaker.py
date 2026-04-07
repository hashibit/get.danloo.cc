"""
Circuit breaker implementation for fault tolerance
"""
import time
import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: int = 60          # Seconds to wait before trying again
    success_threshold: int = 3          # Number of successes to close circuit
    expected_exception: type = Exception  # Exception type to count as failure
    timeout: Optional[float] = None     # Call timeout in seconds


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    total_calls: int
    failed_calls: int
    success_calls: int
    timeout_calls: int


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitTimeoutError(Exception):
    """Exception raised when circuit times out"""
    pass


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
        self.total_calls = 0
        self.failed_calls = 0
        self.success_calls = 0
        self.timeout_calls = 0
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker"""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.total_calls += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker transitioning to HALF_OPEN state")
            else:
                self.timeout_calls += 1
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            # Execute function with timeout if configured
            if self.config.timeout:
                result = self._call_with_timeout(func, self.config.timeout, *args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise
        except TimeoutError as e:
            self._on_timeout()
            raise CircuitTimeoutError(f"Call timed out after {self.config.timeout}s") from e
        except Exception as e:
            self._on_failure()
            raise
    
    def _call_with_timeout(self, func: Callable, timeout: float, *args, **kwargs) -> Any:
        """Execute function with timeout"""
        import signal
        import threading
        
        result = None
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError("Function call timed out")
        
        if exception:
            raise exception
        
        return result
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.success_calls += 1
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        else:
            # Reset failure count on successful call in closed state
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failed_calls += 1
        self.last_failure_time = time.time()
        self.failure_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif self.failure_count >= self.config.failure_threshold:
            self._open_circuit()
    
    def _on_timeout(self):
        """Handle timeout"""
        self.timeout_calls += 1
        self._on_failure()
    
    def _open_circuit(self):
        """Open the circuit"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
    
    def _close_circuit(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker CLOSED after successful recovery")
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics"""
        return CircuitBreakerStats(
            state=self.state,
            failure_count=self.failure_count,
            success_count=self.success_count,
            last_failure_time=self.last_failure_time,
            last_success_time=self.last_success_time,
            total_calls=self.total_calls,
            failed_calls=self.failed_calls,
            success_calls=self.success_calls,
            timeout_calls=self.timeout_calls
        )
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.total_calls = 0
        self.failed_calls = 0
        self.success_calls = 0
        self.timeout_calls = 0
        logger.info("Circuit breaker manually reset")


# Circuit breaker registry for managing multiple circuit breakers
class CircuitBreakerRegistry:
    """Registry for managing circuit breakers"""
    
    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def register(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Register a circuit breaker with a name"""
        if name in self._circuit_breakers:
            logger.warning(f"Circuit breaker '{name}' already exists, returning existing instance")
            return self._circuit_breakers[name]
        
        circuit_breaker = CircuitBreaker(config)
        self._circuit_breakers[name] = circuit_breaker
        logger.info(f"Registered circuit breaker '{name}'")
        return circuit_breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self._circuit_breakers.get(name)
    
    def get_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get stats for all circuit breakers"""
        return {name: cb.get_stats() for name, cb in self._circuit_breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self._circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")
    
    def reset(self, name: str):
        """Reset specific circuit breaker"""
        if name in self._circuit_breakers:
            self._circuit_breakers[name].reset()
            logger.info(f"Circuit breaker '{name}' reset")


# Global registry instance
registry = CircuitBreakerRegistry()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 3,
    expected_exception: type = Exception,
    timeout: Optional[float] = None
):
    """Decorator for circuit breaker protection"""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold,
        expected_exception=expected_exception,
        timeout=timeout
    )
    
    def decorator(func: Callable) -> Callable:
        # Get or create circuit breaker
        cb = registry.register(name, config)
        return cb(func)
    
    return decorator


# Pre-configured circuit breakers for common services
def rate_limit_circuit_breaker():
    """Circuit breaker for rate limiting service"""
    return registry.register(
        "rate_limit_service",
        CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            expected_exception=Exception,
            timeout=1.0
        )
    )


def blacklist_circuit_breaker():
    """Circuit breaker for blacklist service"""
    return registry.register(
        "blacklist_service", 
        CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=3,
            expected_exception=Exception,
            timeout=2.0
        )
    )


def quota_circuit_breaker():
    """Circuit breaker for quota service"""
    return registry.register(
        "quota_service",
        CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=45,
            success_threshold=2,
            expected_exception=Exception,
            timeout=1.5
        )
    )