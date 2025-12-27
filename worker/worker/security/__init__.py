"""
Security module with pluggable validation providers.

This package provides a flexible architecture for path validation and
filename sanitization with support for multiple backend providers.
"""

import logging
import os
from typing import Optional, Set

from .monitoring import (
    OperationTimer,
    PerformanceMonitor,
    SecurityAuditLogger,
    SecurityEventLogger,
    SecurityMetricsCollector,
    get_audit_logger,
    get_event_logger,
    get_metrics_collector,
    get_performance_monitor,
)
from .security_refactor import (
    CustomProvider,
    PathValidateProvider,
    PerformanceMetrics,
    SecurityConfig,
    SecurityError,
    SecurityManager,
    SecurityViolation,
    SecurityViolationType,
    ValidationLevel,
    ValidationProvider,
    ValidationResult,
    WerkzeugProvider,
)

logger = logging.getLogger(__name__)

# Default instance for backward compatibility
_default_manager: SecurityManager | None = None


def get_security_manager(
    config: SecurityConfig | None = None,
) -> SecurityManager:
    """
    Get or create the default security manager.

    Args:
        config: Optional SecurityConfig. If provided, creates a new manager.

    Returns:
        SecurityManager instance
    """
    global _default_manager

    if config is not None:
        _default_manager = SecurityManager(config)
    elif _default_manager is None:
        _default_manager = SecurityManager()

    return _default_manager


def sanitize_filename(filename: str, max_length: int | None = None) -> str:
    """
    Sanitize a filename using the default security manager.

    Args:
        filename: Original filename
        max_length: Maximum allowed length

    Returns:
        Sanitized filename

    Raises:
        ValueError: If filename is invalid
    """
    manager = get_security_manager()
    return manager.sanitize_filename(filename, max_length)


def validate_filename(
    filename: str, max_length: int | None = None
) -> ValidationResult:
    """
    Validate a filename using the default security manager.

    Args:
        filename: Filename to validate
        max_length: Maximum allowed length

    Returns:
        ValidationResult with details
    """
    manager = get_security_manager()
    return manager.validate_filename(filename, max_length)


def is_valid_filename(filename: str) -> bool:
    """
    Check if filename is valid.

    Args:
        filename: Filename to check

    Returns:
        True if valid, False otherwise
    """
    manager = get_security_manager()
    return manager.is_valid_filename(filename)


def validate_uuid(value: str) -> bool:
    """
    Validate if a string is a valid UUID (backward compatible).

    Args:
        value: String to validate

    Returns:
        True if valid UUID, False otherwise
    """
    return SecurityManager._is_valid_uuid(value)


def validate_storage_path(storage_path: str) -> tuple[str, str]:
    """
    Validate and parse a storage path (backward compatible).

    Args:
        storage_path: Path in format "bucket/path/to/file"

    Returns:
        Tuple of (bucket, path)

    Raises:
        SecurityError: If path is invalid
    """
    manager = get_security_manager()
    return manager.validate_storage_path(storage_path)


def validate_bucket_name(bucket: str) -> bool:
    """
    Validate a storage bucket name (backward compatible).

    Args:
        bucket: Bucket name to validate

    Returns:
        True if valid, False otherwise
    """
    manager = get_security_manager()
    return manager.validate_bucket_name(bucket)


def validate_user_path_access(path: str, user_id: str) -> bool:
    """
    Validate that a user can access a specific path (backward compatible).

    Args:
        path: File path to validate
        user_id: User ID requesting access

    Returns:
        True if user can access the path, False otherwise
    """
    manager = get_security_manager()
    return manager.validate_user_path_access(path, user_id)


def create_secure_path(user_id: str, job_id: str, filename: str) -> str:
    """
    Create a secure path for file storage (backward compatible).

    Args:
        user_id: User ID
        job_id: Job ID
        filename: Original filename

    Returns:
        Secure path string

    Raises:
        SecurityError: If any parameter is invalid
    """
    manager = get_security_manager()
    return manager.create_secure_path(user_id, job_id, filename)


def validate_file_extension(
    filename: str, allowed_extensions: Optional[Set[str]] = None
) -> bool:
    """
    Validate file extension against allowed list (backward compatible).

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (with dots)

    Returns:
        True if extension is allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".pdf"}

    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions


__all__ = [
    "SecurityManager",
    "SecurityConfig",
    "SecurityError",
    "ValidationProvider",
    "ValidationResult",
    "SecurityViolation",
    "SecurityViolationType",
    "ValidationLevel",
    "PerformanceMetrics",
    "PathValidateProvider",
    "WerkzeugProvider",
    "CustomProvider",
    "SecurityMetricsCollector",
    "SecurityAuditLogger",
    "PerformanceMonitor",
    "SecurityEventLogger",
    "OperationTimer",
    "get_security_manager",
    "get_metrics_collector",
    "get_audit_logger",
    "get_performance_monitor",
    "get_event_logger",
    "sanitize_filename",
    "validate_filename",
    "is_valid_filename",
    "validate_uuid",
    "validate_storage_path",
    "validate_bucket_name",
    "validate_user_path_access",
    "create_secure_path",
    "validate_file_extension",
]
