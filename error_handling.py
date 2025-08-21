#!/usr/bin/env python3
"""
Enhanced Error Handling for MonoAgent

This module provides comprehensive error handling, recovery strategies,
and resilience features for production MonoAgent deployments.

Features:
- Comprehensive exception handling for edge cases
- Automatic retry mechanisms with exponential backoff
- Graceful degradation strategies
- Error recovery and state restoration
- Detailed error reporting and logging
- Circuit breaker pattern implementation
"""

import functools
import logging
import os
import subprocess
import time
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type, Union
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling."""
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    GIT = "git"
    API = "api"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    operation: str
    retry_count: int = 0
    max_retries: int = 3
    backoff_factor: float = 1.0
    recoverable: bool = True
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MonoAgentError(Exception):
    """Base exception for MonoAgent with enhanced context."""
    
    def __init__(self, message: str, context: ErrorContext = None, cause: Exception = None):
        super().__init__(message)
        self.context = context or ErrorContext(operation="unknown")
        self.cause = cause
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/reporting."""
        return {
            "message": str(self),
            "type": self.__class__.__name__,
            "timestamp": self.timestamp,
            "context": {
                "operation": self.context.operation,
                "retry_count": self.context.retry_count,
                "max_retries": self.context.max_retries,
                "severity": self.context.severity.value,
                "category": self.context.category.value,
                "recoverable": self.context.recoverable,
                "metadata": self.context.metadata
            },
            "cause": str(self.cause) if self.cause else None,
            "traceback": traceback.format_exc()
        }


class NetworkError(MonoAgentError):
    """Network-related errors."""
    
    def __init__(self, message: str, context: ErrorContext = None, cause: Exception = None):
        if context:
            context.category = ErrorCategory.NETWORK
        else:
            context = ErrorContext(operation="network", category=ErrorCategory.NETWORK)
        super().__init__(message, context, cause)


class FilesystemError(MonoAgentError):
    """Filesystem-related errors."""
    
    def __init__(self, message: str, context: ErrorContext = None, cause: Exception = None):
        if context:
            context.category = ErrorCategory.FILESYSTEM
        else:
            context = ErrorContext(operation="filesystem", category=ErrorCategory.FILESYSTEM)
        super().__init__(message, context, cause)


class GitError(MonoAgentError):
    """Git operation errors."""
    
    def __init__(self, message: str, context: ErrorContext = None, cause: Exception = None):
        if context:
            context.category = ErrorCategory.GIT
        else:
            context = ErrorContext(operation="git", category=ErrorCategory.GIT)
        super().__init__(message, context, cause)


class APIError(MonoAgentError):
    """API-related errors."""
    
    def __init__(self, message: str, context: ErrorContext = None, cause: Exception = None):
        if context:
            context.category = ErrorCategory.API
        else:
            context = ErrorContext(operation="api", category=ErrorCategory.API)
        super().__init__(message, context, cause)


class CircuitBreakerOpen(MonoAgentError):
    """Circuit breaker is open, preventing operation."""
    
    def __init__(self, operation: str, failure_count: int):
        context = ErrorContext(
            operation=operation, 
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            metadata={"failure_count": failure_count}
        )
        super().__init__(f"Circuit breaker open for {operation} (failures: {failure_count})", context)


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpen(func.__name__, self.failure_count)
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e
    
    def record_failure(self):
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def reset(self):
        """Reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"


class ErrorHandler:
    """Enhanced error handling with recovery strategies."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_stats: Dict[str, Dict] = {}
    
    def get_circuit_breaker(self, operation: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation."""
        if operation not in self.circuit_breakers:
            self.circuit_breakers[operation] = CircuitBreaker()
        return self.circuit_breakers[operation]
    
    def retry_with_backoff(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        max_backoff: float = 60.0,
        exceptions: tuple = (Exception,),
        circuit_breaker: bool = False
    ):
        """Decorator for retry with exponential backoff."""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                context = ErrorContext(
                    operation=func.__name__,
                    max_retries=max_retries,
                    backoff_factor=backoff_factor
                )
                
                cb = self.get_circuit_breaker(func.__name__) if circuit_breaker else None
                
                for attempt in range(max_retries + 1):
                    context.retry_count = attempt
                    
                    try:
                        if cb:
                            return cb.call(func, *args, **kwargs)
                        else:
                            return func(*args, **kwargs)
                            
                    except exceptions as e:
                        if attempt == max_retries:
                            # Final attempt failed
                            enhanced_error = self._enhance_error(e, context)
                            self._log_error(enhanced_error)
                            self._update_error_stats(enhanced_error)
                            raise enhanced_error
                        
                        # Calculate backoff delay
                        delay = min(backoff_factor * (2 ** attempt), max_backoff)
                        
                        self.logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        
                        time.sleep(delay)
                
            return wrapper
        return decorator
    
    def _enhance_error(self, error: Exception, context: ErrorContext) -> MonoAgentError:
        """Enhance generic exceptions with MonoAgent context."""
        if isinstance(error, MonoAgentError):
            return error
        
        # Categorize error based on type and message
        error_message = str(error).lower()
        
        if isinstance(error, (ConnectionError, TimeoutError)) or "connection" in error_message:
            return NetworkError(str(error), context, error)
        elif isinstance(error, (FileNotFoundError, PermissionError, OSError)) or "file" in error_message:
            return FilesystemError(str(error), context, error)
        elif "git" in error_message or isinstance(error, subprocess.CalledProcessError):
            return GitError(str(error), context, error)
        elif "api" in error_message or "http" in error_message:
            return APIError(str(error), context, error)
        else:
            return MonoAgentError(str(error), context, error)
    
    def _log_error(self, error: MonoAgentError):
        """Log error with enhanced context."""
        error_dict = error.to_dict()
        
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error.context.severity, logging.ERROR)
        
        self.logger.log(
            log_level,
            f"[{error.context.category.value.upper()}][{error.context.severity.value.upper()}] "
            f"{error.context.operation} | {error}"
        )
        
        # Log full context at debug level
        self.logger.debug(f"Error context: {error_dict}")
    
    def _update_error_stats(self, error: MonoAgentError):
        """Update error statistics for monitoring."""
        operation = error.context.operation
        category = error.context.category.value
        
        if operation not in self.error_stats:
            self.error_stats[operation] = {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "last_error": None
            }
        
        stats = self.error_stats[operation]
        stats["total_errors"] += 1
        stats["last_error"] = time.time()
        
        # Update category stats
        if category not in stats["by_category"]:
            stats["by_category"][category] = 0
        stats["by_category"][category] += 1
        
        # Update severity stats
        severity = error.context.severity.value
        if severity not in stats["by_severity"]:
            stats["by_severity"][severity] = 0
        stats["by_severity"][severity] += 1
    
    def graceful_degradation(self, fallback_func: Callable = None, default_value: Any = None):
        """Decorator for graceful degradation."""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.logger.warning(
                        f"Operation {func.__name__} failed, attempting graceful degradation: {e}"
                    )
                    
                    if fallback_func:
                        try:
                            return fallback_func(*args, **kwargs)
                        except Exception as fallback_error:
                            self.logger.error(
                                f"Fallback function also failed for {func.__name__}: {fallback_error}"
                            )
                    
                    if default_value is not None:
                        self.logger.info(f"Returning default value for {func.__name__}")
                        return default_value
                    
                    raise e
            
            return wrapper
        return decorator
    
    def validate_inputs(self, validators: Dict[str, Callable]):
        """Decorator for input validation."""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Get function signature to map args to parameter names
                import inspect
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                for param_name, validator in validators.items():
                    if param_name in bound_args.arguments:
                        value = bound_args.arguments[param_name]
                        try:
                            if not validator(value):
                                raise ValueError(f"Validation failed for parameter '{param_name}': {value}")
                        except Exception as e:
                            context = ErrorContext(
                                operation=func.__name__,
                                category=ErrorCategory.VALIDATION,
                                severity=ErrorSeverity.HIGH,
                                metadata={"parameter": param_name, "value": str(value)}
                            )
                            raise MonoAgentError(f"Input validation failed: {e}", context, e)
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def resource_guard(self, max_memory_mb: float = 1000.0, max_disk_gb: float = 10.0):
        """Decorator to guard against resource exhaustion."""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                import psutil
                
                # Check available resources before operation
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                available_memory_mb = memory.available / 1024 / 1024
                available_disk_gb = disk.free / 1024 / 1024 / 1024
                
                if available_memory_mb < max_memory_mb:
                    context = ErrorContext(
                        operation=func.__name__,
                        category=ErrorCategory.RESOURCE,
                        severity=ErrorSeverity.HIGH,
                        metadata={
                            "available_memory_mb": available_memory_mb,
                            "required_memory_mb": max_memory_mb
                        }
                    )
                    raise MonoAgentError(
                        f"Insufficient memory: {available_memory_mb:.1f}MB available, "
                        f"{max_memory_mb}MB required",
                        context
                    )
                
                if available_disk_gb < max_disk_gb:
                    context = ErrorContext(
                        operation=func.__name__,
                        category=ErrorCategory.RESOURCE,
                        severity=ErrorSeverity.HIGH,
                        metadata={
                            "available_disk_gb": available_disk_gb,
                            "required_disk_gb": max_disk_gb
                        }
                    )
                    raise MonoAgentError(
                        f"Insufficient disk space: {available_disk_gb:.1f}GB available, "
                        f"{max_disk_gb}GB required",
                        context
                    )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        total_errors = sum(stats["total_errors"] for stats in self.error_stats.values())
        
        summary = {
            "total_errors": total_errors,
            "operations_with_errors": len(self.error_stats),
            "by_operation": self.error_stats,
            "circuit_breakers": {
                name: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time
                }
                for name, cb in self.circuit_breakers.items()
            }
        }
        
        return summary


# Utility functions for common validation patterns
def validate_repo_url(url: str) -> bool:
    """Validate repository URL format."""
    if not url or not isinstance(url, str):
        return False
    
    valid_patterns = [
        "https://github.com/",
        "https://gitlab.com/",
        "https://bitbucket.org/",
        "git@github.com:",
        "git@gitlab.com:",
        "git@bitbucket.org:"
    ]
    
    return any(url.startswith(pattern) for pattern in valid_patterns)


def validate_directory_path(path: str) -> bool:
    """Validate directory path."""
    if not path or not isinstance(path, str):
        return False
    
    # Check for path traversal attempts
    if ".." in path or path.startswith("/"):
        return False
    
    # Check for valid characters
    import re
    if not re.match(r'^[a-zA-Z0-9_/.-]+$', path):
        return False
    
    return True


def validate_repo_name(name: str) -> bool:
    """Validate repository name."""
    if not name or not isinstance(name, str):
        return False
    
    # GitHub/GitLab naming rules
    import re
    return bool(re.match(r'^[a-zA-Z0-9_.-]+$', name)) and len(name) <= 100


# Global error handler instance
_global_error_handler = None


def get_error_handler(logger: logging.Logger = None) -> ErrorHandler:
    """Get global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(logger)
    return _global_error_handler


# Convenience decorators using global handler
def retry_on_failure(max_retries: int = 3, backoff_factor: float = 1.0):
    """Convenience decorator for retry logic."""
    handler = get_error_handler()
    return handler.retry_with_backoff(max_retries, backoff_factor)


def graceful_fallback(fallback_func: Callable = None, default_value: Any = None):
    """Convenience decorator for graceful degradation."""
    handler = get_error_handler()
    return handler.graceful_degradation(fallback_func, default_value)


def validate_inputs(**validators):
    """Convenience decorator for input validation."""
    handler = get_error_handler()
    return handler.validate_inputs(validators)


def guard_resources(max_memory_mb: float = 1000.0, max_disk_gb: float = 10.0):
    """Convenience decorator for resource guarding."""
    handler = get_error_handler()
    return handler.resource_guard(max_memory_mb, max_disk_gb)
